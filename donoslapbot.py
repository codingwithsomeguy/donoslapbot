# pylint: disable=missing-function-docstring, consider-using-with
"""donoslapbot was a live coded extra life 2022 donation event bot to
 integrate charitable donations with slapping the streamer over a
 certain amount"""

import os
import json
import asyncio
import urllib.request

from twitchio.ext import commands

# TODONT: pixiefiddler says using donationID in response is safe, from:
#  https://github.com/DonorDrive/PublicAPI/blob/master/resources/donations.md#fields

# this is the same url as DonorDrive, confirmed with npm: extra-life-api
DONATION_API_URL = "https://www.extra-life.org/api/participants/506648/donations"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    + "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
)


def get_sec():
    if "DONOCREDFILE" in os.environ:
        return json.load(open(os.environ["DONOCREDFILE"], encoding="utf-8"))
    raise Exception("export the DONOCREDFILE")


SEC = get_sec()
DONTLOOK = SEC["twitchtoken"]
DONATION_FILENAME = "donations.json"
CURRENT_SLAP_THRESHOLD = 20.0
# testing amount:
# CURRENT_SLAP_THRESHOLD = 5.0


class DonoBot(commands.Bot):
    """DonoBot handles slapping based on EL donations w/chat notifications"""

    def __init__(self):
        # install the task after ready event
        self._poll_donations_task = None
        self._motor_active = False
        # TODO: add pyserial support directly
        # self._serial_port = serial.Serial("/dev/ttyUSB0", 115200)
        # print("throwing away first line:", self._serial_port.readline())
        super().__init__(token=DONTLOOK, prefix="!", initial_channels=["SomeCodingGuy"])

    @commands.command()
    async def extralife(self, ctx: commands.Context):
        mesg = "".join(
            [
                "Extra Life supports the Children's Miracle Network ",
                "Hospitals to fund critical life-saving treatments and ",
                "healthcare services, along with innovative research, ",
                "vital pediatric medical equipment, and child life ",
                "services. See ",
                "https://www.extra-life.org/index.cfm?",
                "fuseaction=donordrive.participant&participantID=506648",
            ]
        )
        await ctx.send(mesg)

    def update_journal(self, latest_api_response):
        new_donations = []
        donations = {}
        if os.path.exists(DONATION_FILENAME):
            donations = json.load(open(DONATION_FILENAME, encoding="utf-8"))
        try:
            donation_data = json.loads(latest_api_response)
            # print(json.dumps(data, indent=2))
            for dent in donation_data:
                # print(dent)
                if (dent["donationID"] in donations) is False:
                    display_name = "Anonymous"
                    if "displayName" in dent:
                        display_name = dent["displayName"]
                    if "amount" not in dent:
                        print("skipping unamounted dono:", dent)
                        continue
                    donation_data = [
                        display_name,
                        float(dent["amount"]),
                        dent["createdDateUTC"],
                    ]
                    donations[dent["donationID"]] = donation_data
                    # new_donation_cb(donation_data)
                    new_donations.append(donation_data)
                else:
                    # TODO: check that amount is there in case it wasn't earlier
                    pass
            # TODO: add ACID compliance
            json.dump(donations, open("donations.json", "w", encoding="utf-8"))

        except json.decoder.JSONDecodeError:
            print("invalid donation response:", latest_api_response)
        return new_donations

    def get_dono_entry(self, donation):
        partial = f"{donation[0]} [${donation[1]}]"
        if donation[1] >= CURRENT_SLAP_THRESHOLD:
            partial += " (SLAP!)"
        return partial

    async def send_new_donation_message(self, channel, new_donations):
        # print("send_new_donation_message: invoked")
        message = "Thank you for your donation"
        if len(new_donations) != 1:
            message += "s"

        message += " "
        message += ", ".join([self.get_dono_entry(dono) for dono in new_donations])
        message += "!!!!"

        # twitchio.errors.InvalidContent: Content must not exceed 500 characters.
        # just truncate for now
        if len(message) > 500:
            message = message[500]

        await channel.send(message)

    def poll_el_dono_api(self):
        request = urllib.request.Request(
            DONATION_API_URL,
            headers={
                "User-Agent": USER_AGENT,
            },
        )
        response = urllib.request.urlopen(request).read()
        # pickle.dump(response, open("donationsresponse2.pkl", "wb"))

        # response = pickle.load(open("donationsresponse1.pkl", "rb"))
        return response

    async def trigger_motor(self):
        if self._motor_active is False:
            self._motor_active = True
            print("trigger_motor: invoked")
            os.system("make")
            self._motor_active = False

    async def process_slaps(self, new_donations):
        for dono in new_donations:
            if dono[1] >= CURRENT_SLAP_THRESHOLD:
                num_slaps_f, _ = divmod(dono[1], CURRENT_SLAP_THRESHOLD)
                num_slaps = round(num_slaps_f)
                for _ in range(num_slaps):
                    await self.trigger_motor()
        await asyncio.sleep(0.1)

    async def poll_donations(self):
        active_channel = self.get_channel("SomeCodingGuy")
        while True:
            print("poll_donations: invoked")
            # print(self.get_context())
            response = self.poll_el_dono_api()
            new_donations = self.update_journal(response)
            if len(new_donations) > 0:
                print("got new_donations:", new_donations)
                await self.send_new_donation_message(active_channel, new_donations)
                await self.process_slaps(new_donations)
            await asyncio.sleep(15)

    async def event_ready(self):
        print("logged in!")

        # TODO: get rid of this
        await asyncio.sleep(1)
        self._poll_donations_task = asyncio.create_task(self.poll_donations())

    async def event_channel_joined(self, channel):
        print("event_channel_joined: channel:", channel)


bot = DonoBot()
bot.run()
