"""Module containing commands which can be used by the bot."""

from bot.math_parser import NumericStringParser
import random
from random import shuffle
import json
import threading

QUOTES_FILE = 'data/quotes.json'
REPLIES_FILE = 'data/sreply_cmds.json'


class Permission:
    """Twitch permissions."""

    User, Subscriber, Moderator, Admin = range(4)


# Base class for a command
class Command(object):
    """Represents a command, a way of reacting to chat messages."""

    perm = Permission.Admin

    def __init__(self, bot):
        """Initialize the command."""
        pass

    def match(self, bot, user, msg):
        """Return whether this command should be run."""
        return False

    def run(self, bot, user, msg):
        """Run this command."""
        pass

    def close(self, bot):
        """Clean up."""
        pass


class SimpleReply(Command):
    """Simple meta-command to output a reply given a specific command. Basic key to value mapping.

    The command list is loaded from a json-file.
    """

    perm = Permission.User

    """load command list"""
    with open(REPLIES_FILE) as fp:
        replies = json.load(fp)

    def match(self, bot, user, msg):
        """Match if command exists."""
        cmd = msg.lower().strip()

        return cmd in self.replies

    def run(self, bot, user, msg):
        """Answer with reply to command."""
        cmd = msg.lower().strip()

        if cmd in self.replies:
            reply = str(self.replies[cmd])
            bot.write(reply)


class EditCommandList(Command):
    """Command to add or remove entries from the command-list.

    Can also be used to display all available commands.
    """

    perm = Permission.Moderator

    """load command list"""
    with open(REPLIES_FILE) as file:
        replies = json.load(file)

    def addcommand(self, bot, cmd):
        """Add a new command to the list, make sure there are no duplicates."""
        tailcmd = cmd[len("!addcommand "):]
        tailcmd.strip()

        """Add all commands in lower case, so no case-sensitive
        duplicates exist."""
        entrycmd = tailcmd.split(" ", 1)[0].lower().strip()
        entryarg = tailcmd.split(" ", 1)[1].strip()

        """Check if the command is already in the list, if not
        add the command to the list"""
        if entrycmd in self.replies:
            bot.write('Command already in the list! DansGame')
        else:
            self.replies[entrycmd] = entryarg

            with open(REPLIES_FILE, 'w') as file:
                json.dump(self.replies, file)

            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write('Command '+entrycmd+' added! FeelsGoodMan')

    def delcommand(self, bot, cmd):
        """Delete an existing command from the list."""
        entrycmd = cmd[len("!delcommand "):]
        entrycmd.strip()

        if entrycmd in self.replies:
            del self.replies[entrycmd]

            with open(REPLIES_FILE, 'w') as file:
                json.dump(self.replies, file)

            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write('Command '+entrycmd+' deleted. FeelsBadMan')
        else:
            bot.write('Command '+entrycmd+' does not exist. monkaS')

    def replylist(self, bot, cmd):
        """Write out the Commandlist in chat."""
        replylist = 'Replylist Commands: '

        for key in self.replies:
            replylist = replylist + key + ' '

        bot.write(str(replylist))

    def match(self, bot, user, msg):
        """Match if !addcommand, !delcommand or !replyList."""
        cmd = msg.lower().strip()
        return cmd.startswith("!addcommand ") or cmd.startswith("!delcommand ") or cmd == "!replylist"

    def run(self, bot, user, msg):
        """Add or delete command, or print list."""

        cmd = msg.lower().strip()

        if cmd.startswith("!addcommand "):
            self.addcommand(bot, msg.strip())
        elif cmd.startswith("!delcommand "):
            self.delcommand(bot, msg.strip())
        elif cmd == "!replylist":
            self.replylist(bot, msg.strip())


class outputQuote(Command):
    """Simple Class to output quotes stored in a json-file."""

    perm = Permission.User

    """load quote list"""
    with open(QUOTES_FILE) as file:
        quotelist = json.load(file)

    def match(self, bot, user, msg):
        """Match if command starts with !quote."""
        cmd = msg.lower().strip()
        return cmd == "!quote" or cmd.startswith("!quote ")

    def run(self, bot, user, msg):
        """Say a quote."""
        cmd = msg.lower().strip()
        if cmd == "!quote":
            quote = random.choice(self.quotelist)
            bot.write(quote)
        elif cmd.startswith("!quote "):
            arg = cmd[len("!quote "):]
            try:
                arg = int(arg.strip()) - 1      # -1: So list for users goes from 1 to len + 1
                if arg >= 0 and arg < len(self.quotelist):
                    quote = self.quotelist[arg]
                    bot.write(quote)
                else:
                    bot.write('Quote not found. Try: !quote [1 - ' + str(len(self.quotelist)) + ']')
            except ValueError:
                bot.write('Wrong input for , try !quote <number>')


class editQuoteList(Command):
    """Add or delete quote from a json-file."""

    perm = Permission.Moderator

    """load quote list"""
    with open(QUOTES_FILE) as file:
        quotelist = json.load(file)

    def addquote(self, bot, msg):
        """Add a quote."""
        quote = msg[len("!addquote "):]
        quote.strip()

        if quote not in self.quotelist:
            self.quotelist.append(quote)
            with open(QUOTES_FILE, 'w') as file:
                json.dump(self.quotelist, file)
            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write('Quote has been added. FeelsGoodMan')
        else:
            bot.write('Quote is already in the list. :thinking:')

    def delquote(self, bot, msg):
        """Delete a quote."""
        quote = msg[len("!delquote "):]
        quote.strip()

        if quote in self.quotelist:
            self.quotelist.remove(quote)
            with open(QUOTES_FILE, 'w') as file:
                json.dump(self.quotelist, file)
            bot.reload_commands()  # Needs to happen to refresh the list.
            bot.write('Quote has been removed. FeelsBadMan')
        else:
            bot.write('Quote not found. :thinking:')

    def match(self, bot, user, msg):
        """Match if message starts with !addquote or !delquote."""
        cmd = msg.lower().strip()
        return cmd.startswith("!addquote ") or cmd.startswith("!delquote ")

    def run(self, bot, user, msg):
        """Add or delete quote."""
        cmd = msg.lower().strip()
        if cmd.startswith("!addquote "):
            self.addquote(bot, msg)
        elif cmd.startswith("!delquote "):
            self.delquote(bot, msg)


class Calculator(Command):
    """A chat calculator that can do some pretty advanced stuff like sqrt and trigonometry.

    Example: !calc log(5^2) + sin(pi/4)
    """

    nsp = NumericStringParser()
    perm = Permission.User

    def match(self, bot, user, msg):
        """Match if the message starts with !calc."""
        return msg.lower().startswith("!calc ")

    def run(self, bot, user, msg):
        """Evaluate second part of message and write the result."""
        expr = msg.split(' ', 1)[1]
        try:
            result = self.nsp.eval(expr)
            if result.is_integer():
                result = int(result)
            reply = "{} = {}".format(expr, result)
            bot.write(reply)
        except TypeError or ValueError:  # Not sure which Errors might happen here.
            bot.write("{} = ???".format(expr))


class Pyramid(Command):
    """Recognizes pyramids of emotes."""

    perm = Permission.User

    count = 0
    currentEmote = ""
    emotes = []

    def match(self, bot, user, msg):
        """Match always."""
        return True

    def pyramidLevel(self, emote, count):
        """Return a pyramid level, made out of the given emote."""
        if count == 1 or count == 5:
            return emote
        if count == 2 or count == 4:
            return emote + ' ' + emote
        if count == 3:
            return emote + ' ' + emote + ' ' + emote

    def run(self, bot, user, msg):
        """Check whether a pyramid was successfully built or a new one was started."""
        self.emotes = bot.emotes
        if self.count == 0:
            if msg in self.emotes:
                self.currentEmote = msg
                self.count = 1
        elif self.count > 0:
            self.count = self.count + 1
            if msg == self.pyramidLevel(self.currentEmote, self.count):
                if(self.count == 5):  # 3 high pyramid
                    self.count = 0
                    bot.write("Yay. " + user.capitalize() + " created a pyramid and gets 30 spam points.")
                    bot.incrementPoints(user, 30)
            elif self.count == 3 and msg == self.pyramidLevel(self.currentEmote, 1):  # 2 high pyramid
                self.count = 0
                if bot.get_permission(user) in [Permission.User, Permission.Subscriber]:
                    bot.write("Wow, " + user.capitalize() + " created a pleb pyramid and gets a free timeout. 4Head")
                    bot.write("/timeout " + user.capitalize() + " 60")
                else:
                    bot.write(user.capitalize() + " created a pleb pyramid and would get a free timeout, but is a mod. FeelsBadMan")
            else:
                if msg in self.emotes:
                    self.count = 1
                    self.currentEmote = msg
                else:
                    self.count = 0


class KappaGame(Command):
    """Play the Kappa game.

    This game consists of guessing a random amount of Kappas.
    """

    perm = Permission.User

    active = False
    n = 0

    def match(self, bot, user, msg):
        """Match if the game is active or gets started with !kstart by a user who pays 5 points."""
        return self.active or startGame(bot, user, msg, "!kstart")

    def run(self, bot, user, msg):
        """Generate a random number n when game gets first started. Afterwards, check if a message contains the emote n times."""
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.n = random.randint(1, 25)
            print("Kappas: " + str(self.n))
            bot.write("Kappa game has started. Guess the right amount of Kappa s between 1 and 25! PogChamp")

        else:
            i = self.countEmotes(cmd, "Kappa")
            if i == self.n:
                bot.write(user.capitalize() + " got it! It was " + str(self.n) + " Kappa s!")
                bot.incrementPoints(user, 7)
                bot.gameRunning = False
                self.active = False
            elif i != -1:
                bot.write("It's not " + str(i) + ". 4Head")

    def countEmotes(self, msg, emote):
        """Count the number of emotes in a message."""
        msg = msg.strip()
        arr = msg.split(' ')
        for e in arr:
            if e != emote:
                return -1
        return len(arr)


class GuessEmoteGame(Command):
    """Play the Guess The Emote Game.

    On Emote is randomly chosen from the list and the users
    have to guess which on it is. Give points to the winner.
    !emotes returns the random emote-list while game is active.
    """

    perm = Permission.User
    active = False
    emotes = []
    emote = ""

    def initGame(self, bot):
        """Initialize GuessEmoteGame: Get all twitch- and BTTV-Emotes, assemble a list of random emotes, choose the winning one."""
        twitchemotes = bot.twitchemotes
        bttvemotes = bot.global_bttvemotes + bot.channel_bttvemotes

        emotelist = []

        n_total = 25
        n_bttv = 10

        i = 0
        while i < (n_total-n_bttv):
            rng_emote = random.choice(twitchemotes)

            if rng_emote not in emotelist:
                emotelist.append(rng_emote)
                i += 1

        i = 0
        while i < n_bttv:
            rng_emote = random.choice(bttvemotes)

            if rng_emote not in emotelist:
                emotelist.append(rng_emote)
                i += 1

        shuffle(emotelist)
        self.emotes = emotelist
        self.emote = random.choice(emotelist)

    def match(self, bot, user, msg):
        """Match if the game is active or gets started with !estart."""
        return self.active or startGame(bot, user, msg, "!estart")

    def run(self, bot, user, msg):
        """Generate a random number n when game gets first started. Afterwards, check if a message contains the emote n times."""
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.initGame(bot)
            print("Right emote: " + self.emote)
            bot.write("The 'Guess The Emote Game' has started. Write one of the following emotes to start playing: " + EmoteListToString(self.emotes))
        else:
            if cmd == self.emote:
                bot.write(user.capitalize() + " got it! It was " + self.emote + " . " + user.capitalize() + " gets 15 spam points.")
                bot.incrementPoints(user, 15)
                bot.gameRunning = False
                self.active = False
            elif cmd == "!emotes":
                bot.write("Possible game emotes: " + EmoteListToString(self.emotes))


def EmoteListToString(emoteList):
    """Convert an EmoteList to a string."""
    s = ""

    for i in range(0, len(emoteList)-1):
        s = s + emoteList[i] + " "

    return s


class GuessMinionGame(Command):
    """Play the Guess The Minion Game.

    One Minion is randomly chosen from the list and the users
    have to guess which on it is. Give points to the winner.
    """

    perm = Permission.User
    active = False

    statToSet = {
        "EXPERT1": "CLASSIC",
        "CORE": "CLASSIC",
        "OG": "WotOG",
        "GANGS": "MSoG",
        "KARA": "OniK"
    }

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
            bot.write("The minion is a " + str(self.minion[stat]).lower() + " card.")
        elif(stat == "set"):
            if (self.statToSet[self.minion[stat]] is not None):
                setname = self.statToSet[self.minion[stat]]
            else:
                setname = str(self.minion[stat])
            bot.write("The card is from the " + setname + " set.")
        elif(stat == "name"):
            bot.write("The name of the card starts with \'" + str(self.minion[stat][0]) + "\'.")
        elif(stat == "rarity"):
            bot.write("The minion is a \'" + str(self.minion[stat]).lower() + "\' card.")
        elif(stat == "attack"):
            bot.write("The minion has " + str(self.minion[stat]) + " attackpower.")
        elif(stat == "cost"):
            bot.write("The card costs " + str(self.minion[stat]) + " mana.")
        elif(stat == "health"):
            if(self.minion[stat] == 1):
                bot.write("The minion has " + str(self.minion[stat]) + " healthpoint.")
            else:
                bot.write("The minion has " + str(self.minion[stat]) + " healthpoints.")

        """Start of threading"""
        self.t = threading.Timer(10, self.giveClue, args=[bot]).start()

    def initGame(self, bot):
        """Initialize GuessMinionGame."""
        self.attributes = ['cardClass', 'set', 'name', 'rarity', 'attack', 'cost', 'health']
        nominion = True
        while nominion:
            self.minion = random.choice(bot.cards)
            if self.minion['type'] == 'MINION':
                nominion = False

        self.timeractive = False

    def match(self, bot, user, msg):
        """Match if the game is active or gets started with !mstart."""
        return self.active or startGame(bot, user, msg, "!mstart")

    def run(self, bot, user, msg):
        """On first run initialize game."""
        cmd = msg.strip()

        if not self.active:
            self.active = True
            self.initGame(bot)
            print("Right Minion: " + self.minion['name'])
            bot.write("The 'Guess The Minion Game' has started. Type minion names to play.")
            self.giveClue(bot)
        else:
            name = self.minion['name'].strip()
            if cmd.strip().lower() == name.lower():
                bot.write(user.capitalize() + " got it! It was " + name + ". " + user.capitalize() + " gets 20 spam points.")
                bot.incrementPoints(user, 20)
                bot.gameRunning = False
                self.active = False
            elif cmd == ("!clue"):
                self.giveClue(bot)

    def close(self, bot):
        """Close minion game."""
        print("TODO: CLOSE MINION GAME.")


class Active(Command):
    """Get active users."""

    perm = Permission.User

    def match(self, bot, user, msg):
        """Match if message starts with !active."""
        return msg.lower().startswith("!active")

    def run(self, bot, user, msg):
        """Write out active users."""
        reply = None
        active = len(bot.get_active_users())

        if active == 1:
            reply = "{}: There is {} active user in chat"
        else:
            reply = "{}: There are {} active users in chat"

        reply = reply.format(user, active)
        bot.write(reply)


class Sleep(Command):
    """Allows admins to pause the bot."""

    perm = Permission.Admin

    def match(self, bot, user, msg):
        """Match if message is !sleep or !wakeup."""
        cmd = msg.lower().strip()
        return cmd.startswith("!sleep") or cmd.startswith("!wakeup")

    def run(self, bot, user, msg):
        """Put the bot to sleep or wake it up."""
        cmd = msg.lower().replace(' ', '')
        if cmd.startswith("!sleep"):
            bot.write("Going to sleep... bye!")
            bot.pause = True
        elif cmd.startswith("!wakeup"):
            bot.write("Good morning everyone!")
            bot.pause = False


def startGame(bot, user, msg, cmd):
    """Return whether a user can start a game.

    Takes off points if a non moderator wants to start a game.
    Also makes sure only one game is running at a time.
    """
    if bot.gameRunning:
        return False
    elif bot.get_permission(user) in [Permission.User, Permission.Subscriber] and msg == cmd:
        # The calling user is not a mod, so we subtract 5 points.
        if(bot.getPoints(user) > 5):
            bot.incrementPoints(user, -5)
            bot.gameRunning = True
            return True
        else:
            bot.write("You need at least 5 points to start a game.")
            return False
    else:  # The calling user is a mod, so we only check if the command is correct
        if msg == cmd:
            bot.gameRunning = True
        return msg == cmd