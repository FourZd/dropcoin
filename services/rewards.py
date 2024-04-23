from sqlalchemy.ext.asyncio import AsyncSession
from models.UserModel import User
from models.AvailableRewards import AvailableReward
from sqlalchemy.future import select
from sqlalchemy.sql import exists, and_
from models.UserReward import UserReward
from models.TwitterPost import TwitterPost
import re
from datetime import datetime, timezone
from models.CrashBet import CrashBet
from configs.environment import get_environment_variables
import httpx
from PIL import Image
from io import BytesIO
async def check_mission(mission_reward: int, user: User, session: AsyncSession, additional_parameter = None):

    if mission_reward == 1:
        """Wallet set up"""
        result = await check_if_wallet_connected(user)

    elif mission_reward == 2:
        """Referrer set up"""
        result = await check_if_referrer_defined(user)

    elif mission_reward == 4:
        """Retweet"""
        # additional_parameter = url
        result = await check_twitter_url(additional_parameter)
        if result:
            new_post = TwitterPost(user_id=user.id, created_at=datetime.now(timezone.utc), post_type="retweet")
            session.add(new_post)
            await session.commit()
    elif mission_reward == 5:
        """Booster in X name"""
        result = await check_twitter_name(user.id)
    elif mission_reward == 6:
        """Twitter post"""
        result = await check_twitter_url(additional_parameter)
        if result:
            new_post = TwitterPost(user_id=user.id, created_at=datetime.now(timezone.utc), post_type="post")
            session.add(new_post)
            await session.commit()
    elif mission_reward == 7:
        """Twitter post"""
        result = await check_twitter_url(additional_parameter)
        if result:
            new_post = TwitterPost(user_id=user.id, created_at=datetime.now(timezone.utc), post_type="post")
            session.add(new_post)
            await session.commit()
    elif mission_reward == 8:
        """PFP booster logo""" # Maybe there's some type of hash
        result = await check_twitter_pfp(user.id)
    elif mission_reward == 9:
        """Follow @Booster_Sol"""
        result = await check_user_following(user.id, "@Booster_Sol")
    elif mission_reward == 10:
        """Follow @DanielKetov"""
        result = await check_user_following(user.id, "@DanielKetov")
    elif mission_reward == 11:
        """Tg group"""
        result = await check_telegram_username(additional_parameter)
        if result:
            user.telegram = additional_parameter
            session.add(user)
            await session.commit()
    elif mission_reward == 12:
        """Play crash"""
        result = await check_user_bet(user.id, session)
    else:
        result = False
    return result

async def check_if_wallet_connected(user: User):
    if user.wallet_address:
        return True
    else:
        return False


async def check_if_referrer_defined(user: User):
    if user.referrer:
        return True
    else:
        return False
    

async def check_user_reward(session: AsyncSession, user_id: int, mission_id: int) -> bool:
    subquery = (
        select([1])
        .where(
            and_(
                UserReward.user_id == user_id,
                UserReward.reward_type_id == mission_id
            )
        )
        .exists()
    )

    result = await session.execute(
        select(subquery.label('mission_completed'))
    )
    mission_completed = result.scalar()
    
    return mission_completed


async def check_twitter_url(url):
    pattern = re.compile(r'https?://twitter\.com/[a-zA-Z0-9_]+/status/\d+')
    if pattern.match(url):
        return True
    else:
        return False
    

async def check_twitter_name(user_id):
    bearer_token = await get_environment_variables().TWITTER_BEARER_TOKEN

    url = f"https://api.twitter.com/2/users/{user_id}"
    headers = {'Authorization': f'Bearer {bearer_token}'}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            user_name = user_data.get('data', {}).get('name', '')
            # Проверка наличия слова 'Booster' в имени пользователя
            return 'Booster' in user_name
        else:
            print(f"Ошибка при запросе к Twitter API: {response.status_code}")
            return False

async def check_twitter_pfp(user_id):
    local_image_path = '../logo.png' 
    result = await check_same_image(local_image_path, user_id)
    return result

async def check_user_following(user_id, account_to_follow):
    # Получение переменных окружения
    bearer_token = await get_environment_variables().TWITTER_BEARER_TOKEN

    if account_to_follow.startswith('@'):
        account_to_follow = account_to_follow[1:]

    url = f"https://api.twitter.com/2/users/{user_id}/following"
    headers = {
        'Authorization': f'Bearer {bearer_token}'
    }
    params = {
        'user.fields': 'username', 
        'max_results': 1000
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            following_list = data.get('data', [])
            # Проверка на наличие username в списке подписок
            is_following = any(user['username'].lower() == account_to_follow.lower() for user in following_list)
            return is_following
        else:
            # Обработка ошибок
            print("Ошибка API:", response.status_code, response.text)
            return False

async def check_user_bet(user_id, session) -> bool:
    stmt = select(exists().where(CrashBet.user_id == user_id))
    result = await session.execute(stmt)
    return result.scalar()


async def check_telegram_username(telegram):
    pattern = re.compile(r'^@([a-zA-Z_][a-zA-Z0-9_]{4,31})$')
    if pattern.match(telegram):
        return True
    else:
        return False
    

async def compare_images(img1, img2):
    if img1.size != img2.size:
        return False
    for x in range(img1.width):
        for y in range(img1.height):
            if img1.getpixel((x, y)) != img2.getpixel((x, y)):
                return False
    return True


async def download_image(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            raise Exception(f"Не удалось загрузить изображение: статус {response.status_code}")
        
def load_local_image(file_path):
    return Image.open(file_path)


def compare_images(img1, img2):
    if img1.size != img2.size:
        return False
    for x in range(img1.width):
        for y in range(img1.height):
            if img1.getpixel((x, y)) != img2.getpixel((x, y)):
                return False
    return True


async def check_same_image(local_image_path, user_id):
    user_image = await fetch_twitter_profile_image_url(user_id)
    local_image = load_local_image(local_image_path)

    if compare_images(user_image, local_image):
        return True
    else:
        return False
    

async def fetch_twitter_profile_image_url(user_id):
    # Подставьте ваш Bearer Token здесь
    bearer_token = await get_environment_variables().TWITTER_BEARER_TOKEN
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }
    url = f"https://api.twitter.com/2/users/{user_id}?user.fields=profile_image_url"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['data']['profile_image_url']
        else:
            raise Exception("Failed to fetch user profile image URL")