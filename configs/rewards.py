from sqlalchemy.ext.asyncio import AsyncSession
from models.AvailableRewards import AvailableReward
from configs.db import get_session


async def create_default_items():
    gen = get_session()
    session = await gen.__anext__()
    if session.query(AvailableReward).count() == 0:
        default_items = [
            AvailableReward( # set up wallet
                title="Share your wallet",
                reward="50", 
                description="Enter Sol wallet where you'd like to receive tokens (not a CEX wallet)",
            ),
            AvailableReward( # referral
                title="May we know who referred you?",
                reward="50", 
                description="Provide the @username of your referrer",
            ),
            AvailableReward( # hard one, referral
                title="Invite friends",
                reward="50", 
                description="Earth airdrop points for everyone who behind your username in 'Hay Khong Who Referred You?' field.\
                Booster features a 2-level referral system: 50 points for each of your buddy, 5 points for each buddy of your buddy.",
            ), 
            AvailableReward( # Retweet
                title="Spread the word about Booster",
                reward="100", 
                description="Retweet", 
            ),
            AvailableReward( # Booster in nickname
                title="Add 'Booster' to your name",
                reward="750", 
                description="Add Booster to your X name",
            ),
            AvailableReward( # ???
                title="Share the hard routine of Booster farmer...",
                reward="100", 
                description="It's time to tell how your day went",
            ),
            AvailableReward( # ???
                title="It's time to tell that the clock is ticking...",
                reward="100", 
                description="Time's almost up, grab your points",
            ),
            AvailableReward( # Profile picture
                title="Change your PFP to Booster logo",
                reward="750", 
                description="Join the army | Download logo:",
            ),
            AvailableReward( # Follow @Booster_Sol
                title="Follow @Booster_Sol",
                reward="75", 
                description="Trust us, this is the follow you won't regret..",
            ),
            AvailableReward( # Follow @DanielKetov
                title="Follow @DanielKetov",
                reward="75", 
                description="You Farm Points, We farm followers, deal?",
            ),
            AvailableReward( # Join TG
                title="It's time to feel some community vibes",
                reward="50", 
                description="Join Booster TG Group -> ",
            ),
            AvailableReward( # Play crash
                title="Play Crash",
                reward="150", 
                description="Let's play crash",
            ),
        ]
        session.bulk_save_objects(default_items)
        await session.commit()