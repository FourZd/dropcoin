from sqlalchemy.ext.asyncio import AsyncSession
from models.UserModel import User
from models.AvailableRewards import AvailableReward
from sqlalchemy.future import select
from sqlalchemy.sql import exists, and_
from sqlalchemy import literal_column
from models.UserReward import UserReward
from models.TwitterPost import TwitterPost
import re
from datetime import datetime, timezone
from models.CrashBet import CrashBet
from configs.environment import get_environment_variables
import httpx
from PIL import Image
from io import BytesIO
from configs.auth import tweepy_client
import tweepy
import asyncio

async def check_mission(mission_reward: int, user: User, session: AsyncSession, additional_parameter = None):

    if mission_reward == 1:
        """Wallet set up"""
        result = await check_if_wallet_connected(user)

    elif mission_reward == 3:
        """Retweet"""
        # additional_parameter = url
        result = await check_twitter_url(additional_parameter)
        if result:
            new_post = TwitterPost(user_id=user.id, created_at=datetime.now(timezone.utc), post_type="retweet", post_url=additional_parameter)
            session.add(new_post)
            await session.commit()
    elif mission_reward == 4:
        """Twitter post"""
        result = await check_twitter_url(additional_parameter)
        if result:
            new_post = TwitterPost(user_id=user.id, created_at=datetime.now(timezone.utc), post_type="post", post_url=additional_parameter)
            session.add(new_post)
            await session.commit()
    elif mission_reward == 5:
        """Twitter post"""
        result = await check_twitter_url(additional_parameter)
        if result:
            new_post = TwitterPost(user_id=user.id, created_at=datetime.now(timezone.utc), post_type="post", post_url=additional_parameter)
            session.add(new_post)
            await session.commit()
    elif mission_reward == 6:
        """Follow @Booster_Sol"""
        await asyncio.sleep(3)
        result = True
    elif mission_reward == 7:
        """Follow @DanielKetov"""
        await asyncio.sleep(3)
        result = True
    elif mission_reward == 8:
        """Tg group"""
        await asyncio.sleep(3)
        result = True
    elif mission_reward == 9:
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
    

async def check_user_reward(session: AsyncSession, user_id: str, mission_id: int) -> bool:
    subquery = (
        select(literal_column("1"))
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
    

async def check_twitter_name(user_id, session):
    # get user auth token and check if user name contains "Booster"
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalars().first()
    try:
        auth = tweepy_client(access=True, access_token=user.access_token, access_token_secret=user.access_token_secret)
        api = tweepy.API(auth)
        user_info = api.verify_credentials()
        user_name = user_info.name
        return 'booster' in user_name.lower()
    except tweepy.TweepError as e:
        print("Ошибка аутентификации:", e)
        return False
async def check_twitter_pfp(user_id, session):
    local_image_path = 'logo.jpg' 
    result = await check_same_image(local_image_path, user_id, session)
    return result

async def check_user_following(user_id, account_to_follow):
    # Получение переменных окружения
    bearer_token = get_environment_variables().TWITTER_BEARER_TOKEN

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
    print("inside comparison")
    if img1.size != img2.size:
        print("Size mismatch")
        print(img1.size, img2.size)
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

async def check_same_image(local_image_path, user_id, session):
    user_image_url = await fetch_twitter_profile_image_url(user_id, session)
    if not user_image_url:
        print("No image")
        return False
    user_image = await download_image(user_image_url)

    local_image = load_local_image(local_image_path)
    
    if await compare_images(user_image, local_image):
        return True
    else:
        return False
    

async def fetch_twitter_profile_image_url(user_id, session):
    # Подставьте ваш Bearer Token здесь
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()
    try:
        auth = tweepy_client(access=True, access_token=user.access_token, access_token_secret=user.access_token_secret)
        api = tweepy.API(auth)
        user_info = api.verify_credentials()
        image_url = user_info.profile_image_url_https
        image_url = image_url.replace('_normal', '_400x400')
        print(image_url)
        return image_url
    except Exception as e:
        print(e)
        return False