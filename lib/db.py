import sqlite3 as db
import Logging as log

class database:
    def __init__(self,conf_db_name):
        try:
            self.conn = db.connect(conf_db_name)
        except Exception as e:
            log.get_logger().log(e.message, level='warn')
        return None


    def create_cursor(self,conn):
        try:
            cursor = conn.cursor()
            return cursor
        except Exception as e:
            log.get_logger().log(e.message, level='warn')

    def create_table(self,cursor,table_name):
        try:
            cursor.execute(table_name)
        except Exception as e:
            log.get_logger().log(e.message, level='warn')

    def insert_data_application(self,cursor,values):
        #cursor.execute("INSERT INTO "+table_name+" VALUES (?,?,?)")
        sql = ''' INSERT INTO Application(App_Name,Global_Flavor,Global_Submitter)
              VALUES(?,?,?) '''

        cursor.execute(sql, values)

    def insert_data_builds(self,cursor,values):
        #cursor.execute("INSERT INTO "+table_name+" VALUES (?,?,?)")
        sql = ''' INSERT INTO Builds(Build_Name,Prefix,Flavors,App_Name)
              VALUES(?,?,?,?) '''

        cursor.execute(sql, values)

    def insert_data_items(self,cursor,values):
        #cursor.execute("INSERT INTO "+table_name+" VALUES (?,?,?)")
        sql = ''' INSERT INTO Items(Item_Name,Inst_Analysis,Builders,Run_Args,Runner,Submitter,Profile_Data,Build_Name)
              VALUES(?,?,?,?,?,?,?,?) '''

        cursor.execute(sql, values)

    def insert_data_experiment(self,cursor,values):
        #cursor.execute("INSERT INTO "+table_name+" VALUES (?,?,?)")
        sql = ''' INSERT INTO Experiment(Experiment_No,Profile_Data,Item_Name)
              VALUES(?,?,?) '''

        cursor.execute(sql, values)