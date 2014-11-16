from collections import defaultdict
import logging
import awirc

from abbb.question import (
    Question, is_question, is_question_end, question_end_users
)


class AntiBoxBoxBot(object):
    BOTNAME = 'boxboxbot'  # lowercase!

    def __init__(self, username, password, database):
        self.client = awirc.Client(
            username, 'irc.twitch.tv', port=6667, password=password
        )

        self.database = database

        self._current_question = None
        self._recorded_messages = defaultdict(set)

    def run(self):
        self.connect()

        self.client.worker.join()

    def connect(self):
        # join flosd channel on startup
        self.client.bind('376', lambda *a: self.client.join_channel('#flosd'))
        self.client.bind('PUBMSG', self.on_pub_msg)

        self.client.connect()

    def on_pub_msg(self, _, source, target, text):
        if source.nick.lower() == self.BOTNAME:
            return self.on_pub_bot_msg(target, text)

        if self._current_question:
            self.record_message(source, text)

    def on_pub_bot_msg(self, target, text):
        logging.debug('BOT: {}'.format(text))

        if is_question(text):
            q = Question.from_text(text)
            logging.info('QUESTION: {!r}'.format(q))

            answer = self.database.get(q)
            if answer:
                logging.info('ANSWER: {}'.format(answer))
                self.client.privmsg(target, answer)
            else:
                self._current_question = q

            return

        if is_question_end(text) and self._current_question:
            answer, users = question_end_users(text)
            if not answer and users:  # someone answered correctly
                answer = self.find_answer(users)

            if answer:
                self._current_question.answer = answer
                self.database.add(self._current_question)

            self._current_question = None
            self._recorded_messages = defaultdict(set)

    def record_message(self, source, text):
        def normalize_answer(text):
            # todo
            return text.strip().lower()

        self._recorded_messages[source.nick.lower()].add(
            normalize_answer(text)
        )

        logging.debug('RECORDED MESSAGE ({}): {}'.format(source.nick, text))

    def find_answer(self, users):
        usernames = [u[0].lower() for u in users]

        if len(usernames) == 1 and \
                not len(self._recorded_messages[usernames[0]]) == 1:
            # only one user answered, but with multiple message
            logging.info('NOT ENOUGH ANSWERS')
            return

        answers = self._recorded_messages[usernames.pop()]
        for username in usernames:
            answers = answers & self._recorded_messages[username]

        logging.info('ANSWERS: {}'.format(answers))

        if len(answers) == 1:
            return answers.pop()

        return None






