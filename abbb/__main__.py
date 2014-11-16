import logging

import abbb.question
import abbb


def main():
    import sys
    import os

    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s:\t%(message)s',
        datefmt='%m/%d/%Y %H:%M:%S', level=logging.DEBUG
    )

    db_path = sys.argv[3]
    if not os.path.exists(db_path):
        abbb.question.QuestionDatabase.create(db_path)

    db = abbb.question.QuestionDatabase(db_path)

    try:
        c = abbb.AntiBoxBoxBot(sys.argv[1], sys.argv[2], db)
        c.run()
    finally:
        db.disconnect()



if __name__ == '__main__':
    main()
