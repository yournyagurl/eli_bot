import sqlite3

class DiscordBotDatabase:
    def __init__(self, db_name="discord_bot.db"):
        self.db_name = db_name
        self.connection = None

    def connect(self):
        """Establish a connection to the database."""
        try:
            self.connection = sqlite3.connect(self.db_name)
            # Enable foreign key constraints
            self.connection.execute('PRAGMA foreign_keys = ON;')
            print(f"Connected to database: {self.db_name}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def create_tables(self):
        """Create the necessary tables for the bot."""
        if not self.connection:
            raise ValueError("No connection to the database. Call connect() first.")
        
        cursor = self.connection.cursor()

        # SQL queries for creating tables
        CREATE_QUERIES = [
            '''
            CREATE TABLE IF NOT EXISTS Members (
                MemberId INTEGER PRIMARY KEY
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS UserActivity (
                MemberId INTEGER,
                MessagesSent INTEGER DEFAULT 0,
                MinutesInVC INTEGER DEFAULT 0,
                XP INTEGER DEFAULT 0,
                FOREIGN KEY (MemberId) REFERENCES Members(MemberId)
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Money (
                MemberId INTEGER,
                Cash INTEGER DEFAULT 0,
                FOREIGN KEY (MemberId) REFERENCES Members(MemberId)
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Income (
                MemberId INTEGER,
                Cash INTEGER DEFAULT 0,
                LastDailyClaim TEXT,
                LastWeeklyClaim TEXT,
                FOREIGN KEY (MemberId) REFERENCES Members(MemberId)
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Shop (
                ItemId INTEGER PRIMARY KEY,
                ItemName TEXT,
                ItemPrice INTEGER,
                ItemConsumable BOOLEAN,
                RoleAssigned INTEGER
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Inventory (
                MemberId INTEGER,
                ItemId INTEGER,
                Quantity INTEGER DEFAULT 1,
                FOREIGN KEY (MemberId) REFERENCES Members(MemberId),
                FOREIGN KEY (ItemId) REFERENCES Shop(ItemId)
            );
            '''
        ]

        try:
            # Run all the queries to create the tables
            for query in CREATE_QUERIES:
                cursor.execute(query)

            # Commit the changes to the database
            self.connection.commit()
            print("Tables created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            self.connection.rollback()

    

    def close(self):
        """Close the database connection."""
        if self.connection:
            try:
                self.connection.close()
                print("Database connection closed.")
            except sqlite3.Error as e:
                print(f"Error closing database connection: {e}")

