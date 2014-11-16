import logging
import sqlite3
import re

#    Next question is : LCS: Who is YellOwStaR's most played Champion(s) during the 2014 EU LCS Spring Regular Season?

_REGEX_QUESTION_END = re.compile(r'(?P<name>\w+)\((?P<points>\d+)\s+points\)')
_REGEX_QUESTION_END2 = re.compile(
    r'congratulations\s+to\s+(?P<name>\w+)\s+for\s+answering\s+first.\s+'
    r'\+(?P<points>\d+)\spoints\s+awarded',
    re.IGNORECASE
)


class Question(object):
    def __init__(self, category, question, answer=None):
        self.category = category.lower()
        self.question = question.lower()
        self.answer = answer.lower() if answer else answer

    def __str__(self):
        return self.question

    def __repr__(self):
        return (
            'Question(category={self.category!r}, '
            'question={self.question!r}, answer={self.answer!r})'
            .format(self=self)
        )

    @staticmethod
    def is_question(text):
        return text.strip().lower().startswith('next question is')

    @classmethod
    def from_text(cls, text):
        if not Question.is_question(text):
            raise ValueError('text {!r} not a question'.format(text))

        _, category, q = map(str.strip, text.split(':', 2))

        return cls(category.lower(), q)


def is_question(text):
    return Question.is_question(text)


def is_question_end(text):
    text = text.strip().lower()
    s = text.startswith('congratulations to') or \
        text.startswith('no one answered correctly')
    e = text.endswith('seconds to next question.') or \
        text.endswith('seconds.')
    return s and e


def question_end_users(text):
    if not is_question_end(text):
        raise ValueError('text {!r} is not a "question end"'.format(text))

    t = text.strip().lower()
    answer = None
    if 'the correct answer was :' in t:
        t = t.split(':', 1)[1]
        answer = t.rsplit('.', 2)[0].strip('"').strip()

    return (
        answer,
        _REGEX_QUESTION_END.findall(text) or _REGEX_QUESTION_END2.findall(text)
    )


class QuestionDatabase(object):
    def __init__(self, path):
        self.path = path

        self.connection = None
        self.cursor = None

        self.connect()

    def connect(self):
        self.connection = sqlite3.connect(self.path)
        self.cursor = self.connection.cursor()

    def disconnect(self):
        self.connection.commit()
        self.connection.close()

        self.cursor = None
        self.connection = None

    def add(self, q):
        if q.answer is None:
            raise ValueError('Question has no answer')

        logging.debug('ADDING QUESTION: {!r}'.format(q))

        self.cursor.execute(
            '''INSERT INTO Question VALUES (?, ?, ?)''',
            (q.question, q.category, q.answer)
        )

        self.connection.commit()

    def get(self, q):
        logging.debug('RETRIEVING QUESTION: {!r}'.format(q))

        self.cursor.execute(
            '''SELECT answer FROM Question WHERE question=? AND category=?''',
            (q.question, q.category)
        )

        result = self.cursor.fetchone()

        return result[0] if result else None

    @staticmethod
    def create(path):
        connection = sqlite3.connect(path)
        cursor = connection.cursor()

        cursor.execute('''
            CREATE TABLE Question (
                question TEXT,
                category TEXT,
                answer TEXT,

                PRIMARY KEY (question, category)
            )
        ''')

        connection.commit()
        connection.close()

    @staticmethod
    def drop(path):
        connection = sqlite3.connect(path)
        cursor = connection.cursor()

        cursor.execute('''
            DROP TABLE Question;
        ''')

        connection.commit()
        connection.close()

