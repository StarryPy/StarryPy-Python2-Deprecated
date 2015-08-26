# -*- coding: UTF-8 -*-

import os
import sqlite3


class DatabaseManager(object):
    def __init__(self, db):
        db_exists = os.path.exists(db)
        self.conn = sqlite3.connect(db)
        if not db_exists:
            self._init_db()

    def __del__(self):
        self.conn.close()

    def _init_db(self):
        sql = """CREATE TABLE IF NOT EXISTS backups (
            planet_coord    TEXT    PRIMARY KEY,
            planet_name     TEXT,
            owner           TEXT,
            active          INT,
            backup_logs     BLOB
        )"""
        self.executescript(sql)

    def select(self, sql, arg):
        cursor = self.conn.cursor()
        if arg:
            cursor.execute(sql, arg)
        else:
            cursor.execute(sql)
        records = cursor.fetchall()
        cursor.close()
        return records

    def insert(self, sql, arg):
        row_id = 0
        cursor = self.conn.cursor()
        if arg:
            cursor.execute(sql, arg)
        else:
            cursor.execute(sql)
        row_id = cursor.lastrowid
        self.conn.commit()
        cursor.close()
        return row_id

    def execute(self, sql, arg):
        cursor = self.conn.cursor()
        if arg:
            cursor.execute(sql, arg)
        else:
            cursor.execute(sql)
        self.conn.commit()
        cursor.close()

    def executescript(self, sql):
        cursor = self.conn.cursor()
        cursor.executescript(sql)
        self.conn.commit()
        cursor.close()
