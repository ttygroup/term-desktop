# from pathlib import Path
# from textual.pilot import Pilot
from term_desktop.main import TermDesktop
# from .app_test import WindowTestApp

async def test_launch():  
    """Test launching the WindowDemo app."""
    app = TermDesktop()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.exit(None) 



# APP_DIR = Path(__file__).parent
# TERINAL_SIZE = (110, 36)


# def test_snapshot_launch_only(snap_compare):

#     async def run_before(pilot: Pilot[None]) -> None:
#         await pilot.pause()

#     assert snap_compare(
#         APP_DIR / "app_test.py",
#         terminal_size=TERINAL_SIZE,
#         run_before=run_before,
#     )