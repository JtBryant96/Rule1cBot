from praw import Reddit
from os import path
from time import sleep
from time import time
from threading import Thread

# user info for the bot
Rule1cBot = Reddit(username='',
                   password='',
                   user_agent='',
                   client_id='',
                   client_secret='')
# path the script is located in (somewhat necessary if your running it on linux)
filePath = ""
# How many post per number of hours is permitted
postsPer = 5
numHours = 6 * 60 * 60


def readFilePosts(fileName):
    """ Return list in the form ["post id's"]

        :param fileName: name of the file used to store
    """
    list_ = []
    if not path.isfile(filePath + fileName):
        f = open(filePath + fileName, "w")
        f.close()
    else:
        with open(filePath + fileName, "r") as f:
            list_ = f.read()
            list_ = list_.split("\n")
            list_ = list(filter(None, list_))
    return list_


def readFileUsers(fileName):
    """ Return list in the form [["author", [TimesInUTC]]]

        :param fileName: name of the file used to store
    """
    list_ = [[]]
    if not path.isfile(filePath + fileName):
        f = open(filePath + fileName, "w")
        f.close()
    else:
        with open(filePath + fileName, "r") as f:
            lines = f.read()
            lines = lines.split("\n")
            lines = list(filter(None, lines))
            list_ = [[]]
            for i in range(len(lines)):
                temp = lines[i].split(" ")
                list_[i].append([temp[0], []])
                for j in range(len(temp)-1):
                    list_[i][j].append(int(temp[j+1]))
    return list_


def pruneList(list_):
    """Removes older timestamps from l

    :param list_: list in the form [["author", [TimesInUTC]]]
    """
    i = 0
    while i < len(list_):
        while True:
            if len(list_[i][1]) == 0:
                list_.pop(i)
                i -= 1
                break
            if list_[i][1][0] + numHours - 300 < time():  # 5 minute leeway
                break
            list_[i][1].pop(0)
        i += 1
        
        
def fileSyncPosts(list_):
    """Syncs list_ to a file in case of a crash.

    :param list_: list in the form ["filename", ["post id's"]]
    """
    list_[1] = list_[1][-50:]
    with open(filePath + list_[0], "w") as f:
        for postId in list_[1]:
            f.write(postId + "\n")


def fileSyncUsers(list_):
    """Syncs list_ to a file in case of a crash.

    :param list_: list in the form ["filename", [["author", [TimesInUTC]]]]
    """
    pruneList(list_)
    with open(filePath + list_[0], "w") as f:
        for user in list_[1]:
            line = user[0]
            for timestamp in user[1]:
                line += " " + timestamp
            f.write(line + "\n")


def authorInList(author, list_):
    """
    :param author: author of post
    :param list_: list in the form [["author", [TimesInUTC]]]
    :return: index of author if in list_, else -1
    """
    for user in list_:
        if user[0] == author:
            list_.index(user)
    return -1


# implemented as thread, so it should be easier be added to another script.
class Rule1cBotThread (Thread):
    def __init__(self, bot, listOfPosts, listOfUsers):
        Thread.__init__(self)
        self.bot = bot
        self.listOfPosts = listOfPosts
        self.listOfUsers = listOfUsers

    def run(self):
        bot = self.bot
        listOfPosts = self.listOfPosts
        listOfUsers = self.listOfUsers
        while True:
            for post in bot.subreddit("ddlc").new(limit=25):
                if post.id not in listOfPosts[1]:
                    i = authorInList(post.author, listOfUsers[1])
                    if i == -1:
                        if len(listOfUsers[1][i][1]) > postsPer:
                            t = numHours - (time() - post.created_utc)
                            # Replace placeholder text
                            post.reply("Looks like you've already posted {numPosts} in the last {numHrs}.\n"
                                       "You can post a new submission in {hr} hours and {min} minutes."
                                       .format(numPosts=postsPer, numHrs=numHours,
                                               hr=int(t/3600), min=int(t / 60 % 60)))
                            post.mod.remove()
                        else:
                            listOfUsers[1][i][1].append(int(post.created_utc))
                    else:
                        listOfUsers[1].append([post.author, [int(post.created_utc)]])
            fileSyncPosts(listOfPosts)
            fileSyncUsers(listOfUsers)
            sleep(120)


def main():
    Rule1cBotThread(Rule1cBot, ["Posts.txt", readFilePosts("Posts.txt")], ["Users.txt", readFileUsers("Users.txt")]).start()


if __name__ == '__main__':
    main()
