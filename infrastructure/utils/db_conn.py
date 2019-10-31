#!/usr/bin/env python3
#
# Copyright 2019 Tigerwing(tigerwingxys@qq.com)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import tornado
import psycopg2
from DBUtils.PersistentDB import PersistentDB

class NoResultError(Exception):
    pass

class NotInitDB(Exception):
    pass


db = None


class DbConnect:
    # Create the global permanent connection.
    @staticmethod
    def init_db(db_host, db_port, db_user, db_password, db_database):
        dsn = 'dbname=%s user=%s password=%s host=%s port=%s' % \
              (db_database, db_user, db_password, db_host, db_port)
        global db
        db = PersistentDB(psycopg2, dsn=dsn)

    @staticmethod
    def get_db_conn():
        global db
        if db is None:
            raise NotInitDB()
        return db.connection()

    @staticmethod
    def row_to_obj(row, cur):
        """Convert a SQL row to an object supporting dict and attribute access."""
        obj = tornado.util.ObjectDict()
        for val, desc in zip(row, cur.description):
            obj[desc.name] = val
        return obj

    @staticmethod
    def execute(stmt, *args):
        """Execute a SQL statement.
        Must be called with ``await self.execute(...)``
        """
        conn = DbConnect.get_db_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(stmt, args)
                return cur.rowcount

    @staticmethod
    def query(stmt, position_offset=0, fetch_size=None, *args):
        """Query for a list of results.
        Typical usage::
            results = await self.query(...)
        Or::
            for row in await self.query(...)
        """
        conn = DbConnect.get_db_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(stmt, args)
                if position_offset > 0:
                    cur.scroll(position_offset, mode="absolute")
                if fetch_size is None:
                    cds = cur.fetchall()
                else:
                    cds = cur.fetchmany(fetch_size)
                results = [DbConnect.row_to_obj(row, cur) for row in cds]
        return results

    @staticmethod
    def query_check(stmt, *args):
        """Query for a check, return if exists.
        Typical usage::
            some_row_exists = await self.query_check(...)
        """
        conn = DbConnect.get_db_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(stmt, args)
                cur.fetchone()
                result = cur.rowcount
        return result > 0

    @staticmethod
    def query_one(stmt, *args):
        """Query for exactly one result.
        Raises NoResultError if there are no results, or ValueError if
        there are more than one.
        """
        conn = DbConnect.get_db_conn()
        with conn:
            with conn.cursor() as cur:
                obj = tornado.util.ObjectDict()
                cur.execute(stmt, args)
                cds = cur.fetchone()
                if cur.rowcount == 0:
                    cur.close()
                    raise NoResultError()

                i = 0
                for desc in cur.description:
                    obj[desc.name] = cds[i]
                    i += 1
        return obj

    @staticmethod
    def execute_returning(stmt, *args):
        """Execute and exactly with returning one result.
        Raises NoResultError if there are no results, or ValueError if
        there are more than one.
        """
        conn = DbConnect.get_db_conn()
        with conn:
            with conn.cursor() as cur:
                obj = tornado.util.ObjectDict()
                cur.execute(stmt, args)
                cds = cur.fetchone()
                if cur.rowcount == 0:
                    cur.close()
                    raise NoResultError()

                i = 0
                for desc in cur.description:
                    obj[desc.name] = cds[i]
                    i += 1
        return obj


def begin_transaction():
    DbConnect.get_db_conn().begin()


def commit_transaction():
    DbConnect.get_db_conn().commit()


def rollback_transaction():
    DbConnect.get_db_conn().rollback()
