import sqlite3 as db

sql_create_application_table = """ CREATE TABLE IF NOT EXISTS Application (
                                        App_Name text PRIMARY KEY,
                                        Global_Flavor text NOT NULL,
                                        Global_Submitter text NOT NULL
                                    ); """

sql_create_builds_table = """ CREATE TABLE IF NOT EXISTS Builds (
                                        Build_Name text PRIMARY KEY,
                                        Prefix text NOT NULL,
                                        Flavors text NOT NULL,
                                        App_Name text FOREIGN KEY 
                                    ); """

sql_create_items_table = """ CREATE TABLE IF NOT EXISTS Items (
                                        Item_Name text PRIMARY KEY,
                                        Inst_Analysis text NOT NULL,
                                        Builders text NOT NULL,
                                        Run_Args text NOT NULL,
                                        Runner text NOT NULL,
                                        Submitter text NOT NULL,
                                        Profile_Data text NOT NULL,
                                        Build_Name text FOREIGN KEY
                                    ); """

sql_create_builds_table = """ CREATE TABLE IF NOT EXISTS Items (
                                        Item_Name text PRIMARY KEY,
                                        Inst_Analysis text NOT NULL,
                                        Builders text NOT NULL,
                                        Run_Args text NOT NULL,
                                        Runner text NOT NULL,
                                        Submitter text NOT NULL,
                                        Profile_Data text NOT NULL,
                                        Build_Name text FOREIGN KEY
                                    ); """

sql_create_experiment_table = """ CREATE TABLE IF NOT EXISTS Experiment (
                                        Experiment_No INTEGER PRIMARY KEY,
                                        Profile_Data text NOT NULL,
                                        Item_Name text FOREIGN KEY 
                                    ); """