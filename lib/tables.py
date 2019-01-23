import sqlite3 as db

create_application_table = """ CREATE TABLE IF NOT EXISTS Application (
                                        AppID text PRIMARY KEY,
                                        App_Name text,
                                        Global_Flavor text,
                                        Global_Submitter text
                                    ); """

create_builds_table = """ CREATE TABLE IF NOT EXISTS Builds (
                                        BuildID text PRIMARY KEY,
                                        Build_Name text NOT NULL,
                                        Prefix text NOT NULL,
                                        Flavors text NOT NULL,
                                        AppName text NOT NULL,
                                        FOREIGN KEY(AppName) REFERENCES Application(App_Name)
                                    ); """

create_items_table = """ CREATE TABLE IF NOT EXISTS Items (
                                        ItemID text PRIMARY KEY,
                                        Item_Name text NOT NULL,
                                        Inst_Analysis_Functor_Path text NOT NULL,
                                        Builders_Funtor_Path text NOT NULL,
                                        Run_Args text NOT NULL,
                                        Runner_Functor_Path text NOT NULL,
                                        Submitter_Functor_Path text NOT NULL,
                                        Exp_Data_Dir_Base_Path text NOT NULL,
                                        BuildName text NOT NULL,
                                        FOREIGN KEY(BuildName) REFERENCES Builds(Build_Name)
                                    ); """

create_experiment_table = """ CREATE TABLE IF NOT EXISTS Experiment (
                                        Experiment_ID text PRIMARY KEY,
                                        BenchmarkName text,
                                        Iteration_No INTEGER,
                                        IsWithInstrumentation INTEGER,
                                        CubeFilePath text NOT NULL,
                                        Runtime text NOT NULL,
                                        Item_ID text NOT NULL,
                                        FOREIGN KEY(Item_ID) REFERENCES Items(ItemID)
                                    ); """
