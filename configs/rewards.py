from sqlalchemy.ext.asyncio import AsyncSession
from models.AvailableRewards import AvailableReward
from configs.db import get_session
from sqlalchemy.future import select

async def create_default_items():
    gen = get_session()
    session = await gen.__anext__()
    stmt = select(AvailableReward)
    result = await session.execute(stmt)
    reward_count = len(result.scalars().all())

    if reward_count == 0:
        default_items = [
            AvailableReward(
                title="Share your wallet",
                reward=50,
                description="Enter Sol wallet where you'd like to receive tokens (not a CEX wallet)"
            ),
            AvailableReward(
                title="May we know who referred you?",
                reward=50,
                description="Provide the @username of your referrer"
            ),
            AvailableReward(
                title="Invite friends",
                reward=50,
                description="Earn airdrop points for everyone who mentions your username in 'Who Referred You?' field."
                            " Booster features a 2-level referral system: 50 points for each of your buddy, 5 points for each buddy of your buddy."
            ),
            AvailableReward(
                title="Spread the word about Booster",
                reward=100,
                description="Retweet"
            ),
            AvailableReward(
                title="Add 'Booster' to your name",
                reward=750,
                description="Add 'Booster' to your X name"
            ),
            AvailableReward(
                title="Share the hard routine of Booster farmer...",
                reward=100,
                description="It's time to tell how your day went"
            ),
            AvailableReward(
                title="It's time to tell that the clock is ticking...",
                reward=100,
                description="Time's almost up, grab your points"
            ),
            AvailableReward(
                title="Change your PFP to Booster logo",
                reward=750,
                description="Join the army | Download logo:"
            ),
            AvailableReward(
                title="Follow @Booster_Sol",
                reward=75,
                description="Trust us, this is the follow you won't regret."
            ),
            AvailableReward(
                title="Follow @DanielKetov",
                reward=75,
                description="You Farm Points, We farm followers, deal?"
            ),
            AvailableReward(
                title="It's time to feel some community vibes",
                reward=50,
                description="Join Booster TG Group -> "
            ),
            AvailableReward(
                title="Play Crash",
                reward=150,
                description="Let's play crash"
            ),
            AvailableReward(
                title="Referrer of the referrer",
                reward=5,
                description="A user who invited the user who invited you"
            )
        ]
        for item in default_items:
            session.add(item)
        await session.commit()