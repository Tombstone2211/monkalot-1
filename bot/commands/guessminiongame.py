"""Commands: "!mstart", "!mstop"."""
import random

from twisted.internet import reactor

from bot.commands.command import Command
from bot.utilities.permission import Permission
from bot.utilities.startgame import startGame
from bot.utilities.tools import is_callID_active


class GuessMinionGame(Command):
    """Play the Guess The Minion Game.

    One Minion is randomly chosen from the list and the users
    have to guess which on it is. Give points to the winner.
    """

    perm = Permission.User

    def __init__(self, bot):
        """Initialize variables."""
        self.responses = {}
        self.active = False
        self.cluetime = 10   # time between clues in seconds
        self.callID = None
        self.statToSet = {}

    def giveClue(self, bot): # noqa (let's ignore the high complexity for now)
        """Give a random clue to the chat.

        This stops the threading once all clues have been
        given or the game is over.
        """
        if (not self.attributes) or (not self.active):
            return

        stat = random.choice(self.attributes)
        self.attributes.remove(stat)

        """ Write a clue in chat. Some set names have to be renamed. """
        if(stat == "cardClass"):
            var = {"<STAT>": str(self.minion[stat]).lower()}
            bot.write(bot.replace_vars(self.responses["clue_stat"]["msg"], var))
        elif(stat == "set"):
            self.statToSet = self.responses["setnames"]["msg"]
            if self.minion[stat] in self.statToSet:
                setname = self.statToSet[self.minion[stat]]
            else:
                setname = str(self.minion[stat])
            var = {"<STAT>": setname}
            bot.write(bot.replace_vars(self.responses["clue_set"]["msg"], var))
        elif(stat == "name"):
            var = {"<STAT>": self.minion[stat][0]}
            bot.write(bot.replace_vars(self.responses["clue_letter"]["msg"], var))
        elif(stat == "rarity"):
            var = {"<STAT>": str(self.minion[stat]).lower()}
            bot.write(bot.replace_vars(self.responses["clue_rarity"]["msg"], var))
        elif(stat == "attack"):
            var = {"<STAT>": self.minion[stat]}
            bot.write(bot.replace_vars(self.responses["clue_attackpower"]["msg"], var))
        elif(stat == "cost"):
            var = {"<STAT>": self.minion[stat]}
            bot.write(bot.replace_vars(self.responses["clue_manacost"]["msg"], var))
        elif(stat == "health"):
            if(self.minion[stat] == 1):
                var = {"<STAT>": self.minion[stat], "<PLURAL>": ""}
            else:
                var = {"<STAT>": self.minion[stat], "<PLURAL>": "s"}
            bot.write(bot.replace_vars(self.responses["clue_healthpoints"]["msg"], var))

        """Start of threading"""
        self.callID = reactor.callLater(self.cluetime, self.giveClue, bot)

    def initGame(self, bot):
        """Initialize GuessMinionGame."""
        self.attributes = ['cardClass', 'set', 'name', 'rarity', 'attack', 'cost', 'health']
        nominion = True
        while nominion:
            self.minion = random.choice(bot.getHearthstoneCards())
            if self.minion['type'] == 'MINION':
                nominion = False

    def match(self, bot, user, msg, tag_info):
        """Match if the game is active or gets started with !mstart."""
        return self.active or startGame(bot, user, msg, "!mstart")

    def run(self, bot, user, msg, tag_info):
        """On first run initialize game."""
        self.responses = bot.responses["GuessMinionGame"]
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.initGame(bot)
            print("Right Minion: " + self.minion['name'])
            bot.write(self.responses["start_msg"]["msg"])
            self.giveClue(bot)
        else:
            if cmd == "!mstop" and bot.get_permission(user) not in [Permission.User, Permission.Subscriber]:
                self.close(bot)
                bot.write(self.responses["stop_msg"]["msg"])
                return

            name = self.minion['name'].strip()
            if cmd.strip().lower() == name.lower():
                var = {"<USER>": bot.displayName(user), "<MINION>": name, "<PRONOUN0>": bot.pronoun(user)[0].capitalize(), "<AMOUNT>": bot.MINIONGAMEP}
                bot.write(bot.replace_vars(self.responses["winner_msg"]["msg"], var))
                bot.ranking.incrementPoints(user, bot.MINIONGAMEP, bot)
                self.close(bot)

    def close(self, bot):
        """Close minion game."""
        if is_callID_active(self.callID):
            self.callID.cancel()
        self.active = False
        bot.gameRunning = False
