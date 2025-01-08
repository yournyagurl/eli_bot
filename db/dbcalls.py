import sqlite3
from db.database import DiscordBotDatabase
import datetime
import time

class DiscordBotCrud:
    def __init__(self, db_name="discord_bot.db"):
        """Initialize the CRUD class with the database connection."""
        self.db = DiscordBotDatabase(db_name)
        self.db.connect()
        self.ensure_table_exists()

        # Dictionary to store join times for users
        self.user_voice_times = {}

    def ensure_table_exists(self):
        """Ensure that the Members table exists."""
        cursor = self.db.connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Members (
            MemberId INTEGER PRIMARY KEY
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS UserActivity (
            MemberId INTEGER PRIMARY KEY,
            MessagesSent INTEGER DEFAULT 0,
            XP INTEGER DEFAULT 0,
            LastMessageTime DATETIME DEFAULT CURRENT_TIMESTAMP,
            LastVCTimestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            MinutesInVC INTEGER DEFAULT 0
        );
        """)
        cursor.execute("PRAGMA foreign_keys = ON;")
        self.db.connection.commit()

    def add_member(self, member_id):
        """Add a new member to the Members and UserActivity tables."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("INSERT OR IGNORE INTO Members (MemberId) VALUES (?);", (member_id,))
            cursor.execute("INSERT OR IGNORE INTO UserActivity (MemberId) VALUES (?);", (member_id,))# Add entry to UserActivity table
            cursor.execute("INSERT OR IGNORE INTO Income (MemberId) VALUES (?);", (member_id,))  # add entry to income table
            cursor.execute("INSERT OR IGNORE INTO Money (MemberId) VALUES (?);", (member_id,)) # add entry into money table 
            cursor.execute("INSERT OR IGNORE INTO Inventory (MemberId) VALUES (?);", (member_id,)) # add entry into inventory

            self.db.connection.commit()
            print(f"Member {member_id} added.")
        except sqlite3.DatabaseError as e:
            print(f"Error adding member {member_id}: {e}")
            self.db.connection.rollback()

    def remove_member(self, member_id):
        """Remove a member from the Members and dependent tables when they leave the server."""
        try:
            cursor = self.db.connection.cursor()

            # Delete from dependent tables first to avoid foreign key constraint issues
            cursor.execute("DELETE FROM Inventory WHERE MemberId = ?;", (member_id,))
            cursor.execute("DELETE FROM Money WHERE MemberId = ?;", (member_id,))
            cursor.execute("DELETE FROM Income WHERE MemberId = ?;", (member_id,))
            cursor.execute("DELETE FROM UserActivity WHERE MemberId = ?;", (member_id,))
            
            # Now remove from the Members table
            cursor.execute("DELETE FROM Members WHERE MemberId = ?;", (member_id,))
            self.db.connection.commit()

            print(f"Member {member_id} and related data removed.")
        except sqlite3.DatabaseError as e:
            print(f"Error removing member {member_id}: {e}")
            self.db.connection.rollback()

    def get_member(self, member_id):
        """Retrieve member information from the Members table."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT * FROM Members WHERE MemberId = ?", (member_id,))
            return cursor.fetchone()
        except sqlite3.DatabaseError as e:
            print(f"Error retrieving member {member_id}: {e}")
            return None

    def increment_messages_sent(self, member_id):
        try:
            cursor = self.db.connection.cursor()
            # Check if the user exists
            cursor.execute("SELECT MessagesSent, XP FROM UserActivity WHERE MemberId = ?", (member_id,))
            result = cursor.fetchone()

            if result:
                # Update MessagesSent and LastMessageTimestamp if the user exists
                cursor.execute("""
                    UPDATE UserActivity
                    SET MessagesSent = MessagesSent + 1, XP = XP + 1, LastMessageTime = CURRENT_TIMESTAMP
                    WHERE MemberId = ?;
                """, (member_id,))
            else:
                # Insert new record with MessagesSent = 1 if the user doesn't exist
                cursor.execute("""
                    INSERT INTO UserActivity (MemberId, MessagesSent, XP, LastMessageTime)
                    VALUES (?, 1, 1, CURRENT_TIMESTAMP);
                """, (member_id,))

            self.db.connection.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            cursor.close()

    def update_xp(self, member_id, new_xp):
        """Update the user's XP in the database."""
        cursor = self.db.connection.cursor()
        cursor.execute("UPDATE UserActivity SET XP = ? WHERE MemberId = ?;", (new_xp, member_id))
        self.db.connection.commit()
        print(f"Updated XP for Member {member_id} to {new_xp}.")

    

    def get_user_activity(self, member_id):
        """Retrieve a user's activity information from the UserActivity and Money tables."""
        try:
            cursor = self.db.connection.cursor()

            # Query to get the user's activity and cash
            cursor.execute("""
                SELECT 
                    ua.MessagesSent, 
                    ua.XP, 
                    ua.MinutesInVC, 
                    m.Cash 
                FROM 
                    UserActivity ua
                LEFT JOIN 
                    Money m 
                ON 
                    ua.MemberId = m.MemberId
                WHERE 
                    ua.MemberId = ?;
            """, (member_id,))
            result = cursor.fetchone()

            if result:
                # Return the result as a dictionary-like object for easier access
                return {
                    'MessagesSent': result[0],     # Number of messages sent
                    'XP': result[1],               # Total XP earned
                    'MinutesInVC': result[2],      # Total time spent in voice chat
                    'Cash': result[3]              # Cash value from Money table
                }
            else:
                # Return None if no data is found for the user
                return None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            cursor.close()


    def get_top_chat_users(self, days=7):
        try:
            cursor = self.db.connection.cursor()

            # Query for the last 7 days
            cursor.execute("""
                SELECT MemberId, MessagesSent 
                FROM UserActivity
                WHERE LastMessageTime >= DATETIME('now', ?)
                ORDER BY MessagesSent DESC
                LIMIT 10;
            """, (f"-{days} days",))
            recent_data = cursor.fetchall()

            if recent_data:
                return recent_data  # Return recent data if available
            else:
                # Fallback to all-time data
                cursor.execute("""
                    SELECT MemberId, MessagesSent 
                    FROM UserActivity
                    ORDER BY MessagesSent DESC
                    LIMIT 10;
                """)
                all_time_data = cursor.fetchall()
                return all_time_data

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()

    def get_top_voice_users(self, days=7):
        try:
            cursor = self.db.connection.cursor()

            # Query for the last 7 days
            cursor.execute("""
                SELECT MemberId, MinutesInVC 
                FROM UserActivity
                WHERE LastVCTimestamp >= DATETIME('now', ?)
                ORDER BY MinutesInVC DESC
                LIMIT 10;
            """, (f"-{days} days",))
            recent_data = cursor.fetchall()

            if recent_data:
                return recent_data  # Return recent data if available
            else:
                # Fallback to all-time data
                cursor.execute("""
                    SELECT MemberId, MinutesInVC 
                    FROM UserActivity
                    ORDER BY MinutesInVC DESC
                    LIMIT 10;
                """)
                all_time_data = cursor.fetchall()
                return all_time_data

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()

    def get_top_xp(self):
        try:
            cursor = self.db.connection.cursor()

            # Query for the last 7 days
            cursor.execute("""
                SELECT MemberId, XP 
                FROM UserActivity
                ORDER BY XP DESC
                LIMIT 9;
            """)

            # Fetch all the results
            top_xp_data = cursor.fetchall()

            # If there are top users, return them as a list of tuples (MemberId, XP)
            return top_xp_data if top_xp_data else []

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()


    def add_xp(self, member_id, xp_amt):
        try:
            cursor = self.db.connection.cursor()

            cursor.execute('''
            UPDATE UserActivity
            SET XP = XP + ?
            WHERE MemberId = ?''', (xp_amt, member_id))

            self.db.connection.commit()
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()
    
    def remove_xp(self, member_id, xp_amt):
        try:
            cursor = self.db.connection.cursor()

            cursor.execute('''
            UPDATE UserActivity
            SET XP = XP - ?
            WHERE MemberId = ?''', (xp_amt, member_id))

            self.db.connection.commit()
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()

    def add_cash(self, member_id, cash_amt):
        try:
            cursor = self.db.connection.cursor()

            cursor.execute('''
            UPDATE Money
            SET Cash = Cash + ?
            WHERE MemberId = ?''', (cash_amt, member_id))

            self.db.connection.commit()
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()

    def remove_cash(self, member_id, cash_amt):
        try:
            cursor = self.db.connection.cursor()

            cursor.execute('''
            UPDATE Money
            SET Cash = Cash - ?
            WHERE MemberId = ?''', (cash_amt, member_id))

            self.db.connection.commit()
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()

    def reset_cash(self, member_id, new_cash):
        try:
            cursor = self.db.connection.cursor()
            cursor.execute('''UPDATE Money SET Cash = ? WHERE MemberId = ?''', (new_cash, member_id))
            self.db.connection.commit()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
                cursor.close()
            
    def get_lastclaimtime(self, member_id, claim_type):
        try:
            cursor = self.db.connection.cursor()
            column = 'LastDailyClaim' if claim_type == 'daily' else 'LastWeeklyClaim'
            cursor.execute(f'SELECT {column} FROM Income WHERE MemberId = ?', (member_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
                cursor.close()

    def update_lastclaimtime(self, member_id, claim_type, time):
        try:
            cursor = self.db.connection.cursor()
            column = 'LastDailyClaim' if claim_type == 'daily' else 'LastWeeklyClaim'
        
            # Check if the record already exists
            cursor.execute(f'SELECT 1 FROM Income WHERE MemberId = ?', (member_id,))
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Update the existing record
                cursor.execute(f'''
                    UPDATE Income 
                    SET {column} = ?
                    WHERE MemberId = ?
                ''', (time, member_id))
            else:
                # Insert a new record
                cursor.execute(f'''
                    INSERT INTO Income (MemberId, {column}) 
                    VALUES (?, ?)
                ''', (member_id, time))
            
            self.db.connection.commit()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
                cursor.close()
        



            
    def get_top_cash(self):
        try:
            cursor = self.db.connection.cursor()

            # Query for the last 7 days
            cursor.execute("""
                SELECT MemberId, Cash 
                FROM Money
                ORDER BY Cash DESC
                LIMIT 9;
            """)

            # Fetch all the results
            top_cash_data = cursor.fetchall()

            # If there are top users, return them as a list of tuples (MemberId, XP)
            return top_cash_data if top_cash_data else []

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()

    def get_inventory(self, member_id):
        try:
            cursor = self.db.connection.cursor()

            cursor.execute('''
            SELECT s.ItemName, i.Quantity
            FROM Inventory i
            JOIN Shop s ON i.ItemId = s.ItemId
            WHERE i.MemberId = ?''', (member_id,))
            
            results = cursor.fetchall()

            return results
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()

    def get_shop_items(self):

        try:
            cursor = self.db.connection.cursor()

            cursor.execute('''
            SELECT ItemName, ItemPrice
            FROM Shop''')
            
            results = cursor.fetchall()

            return results

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()

    def add_shop_item(self, name, price, consumable, role_assigned=None):
        try:
            cursor = self.db.connection.cursor()
            cursor.execute('''
                INSERT INTO Shop (ItemName, ItemPrice, ItemConsumable, RoleAssigned)
                VALUES (?, ?, ?, ?)
            ''', (name, price, consumable, role_assigned))
            self.db.connection.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            cursor.close()

    
    def delete_shop_item(self, item_name):
        try:
            cursor = self.db.connection.cursor()

            # Ensure the item exists first (check for exact match)
            cursor.execute('''SELECT ItemName, ItemId FROM Shop WHERE LOWER(ItemName) = LOWER(?)''', (item_name,))
            item = cursor.fetchone()

            if not item:
                # If no matching item is found, return False
                print(f"Item '{item_name}' not found in the shop.")
                return False  # Item not found, return False

            item_id = item[1]  # Get the ItemId of the item to be deleted

            # Delete the related entries in the Inventory table
            cursor.execute('''DELETE FROM Inventory WHERE ItemId = ?''', (item_id,))

            # Proceed with deleting the item from the Shop table
            cursor.execute('''DELETE FROM Shop WHERE LOWER(ItemName) = LOWER(?)''', (item_name,))
            self.db.connection.commit()

            # Check if the deletion was successful
            rows_affected = cursor.rowcount
            if rows_affected > 0:
                print(f"Item '{item_name}' successfully deleted from the shop.")
                return True  # Successful deletion
            else:
                print(f"Item '{item_name}' could not be deleted (no rows affected).")
                return False  # No rows affected, deletion failed

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False  # Return False on error
        finally:
            cursor.close()


    
    def add_inventory_item(self, member_id, item_name):
        try:
            cursor = self.db.connection.cursor()

    # Get the item ID from the Shop table
            cursor.execute('''
            SELECT ItemId
            FROM Shop
            WHERE ItemName = ?''', (item_name,))
            result = cursor.fetchone()
            if not result:
                # If the item doesn't exist in the shop, do nothing
                return

            item_id = result[0]

            # Check if the member already has the item in their inventory
            cursor.execute('''
            SELECT COUNT(*)
            FROM Inventory
            WHERE MemberId = ? AND ItemId = ?''', (member_id, item_id))
            result = cursor.fetchone()
            if result and result[0] > 0:
                # If the member already has the item, increase the quantity by 1
                cursor.execute('''
                UPDATE Inventory
                SET Quantity = Quantity + 1
                WHERE MemberId = ? AND ItemId = ?''', (member_id, item_id))
            else:
                # Otherwise, add a new row to the Inventory table with quantity 1
                cursor.execute('''
                INSERT INTO Inventory (MemberId, ItemId, Quantity)
                VALUES (?, ?, 1)''', (member_id, item_id))

            self.db.connection.commit()
        except sqlite3.Error as e:
                print(f"Database error: {e}")
                return []
        finally:
            cursor.close()


    def use_inventory_item(self, member_id, item_name):
        try:
            cursor = self.db.connection.cursor()

            # Get the item ID and effects from the Shop table
            cursor.execute('''
            SELECT ItemId, ItemConsumable, RoleAssigned
            FROM Shop
            WHERE ItemName = ?''', (item_name,))
            result = cursor.fetchone()
            if not result:
                raise ValueError("Item not found in shop.")
            
            item_id, consumable, role_assigned = result

            # Check if the user has the item in their inventory
            cursor.execute('''
            SELECT Quantity
            FROM Inventory
            WHERE MemberId = ? AND ItemId = ?''', (member_id, item_id))
            result = cursor.fetchone()
            if not result or result[0] <= 0:
                raise ValueError("Item not found in inventory or quantity is zero.")

            quantity = result[0]

            # If the item is consumable, decrease its quantity
            if consumable:
                new_quantity = quantity - 1
                if new_quantity <= 0:
                    cursor.execute('''
                    DELETE FROM Inventory
                    WHERE MemberId = ? AND ItemId = ?''', (member_id, item_id))
                else:
                    cursor.execute('''
                    UPDATE Inventory
                    SET Quantity = ?
                    WHERE MemberId = ? AND ItemId = ?''', (new_quantity, member_id, item_id))

            self.db.connection.commit()

            return role_assigned  # Return the role name or ID associated with the item

        except sqlite3.Error as e:
            raise  # Re-raise the exception to be handled in the command function
        except ValueError as ve:
            raise  # Raise ValueError to indicate item not found or quantity issue
        finally:
            cursor.close()

        return None
    
    def get_cash(self, member_id):
        cursor = self.db.connection.cursor()
        try:
            # Query to get the user's cash balance
            cursor.execute("SELECT Cash FROM Money WHERE MemberId = ?", (member_id,))
            result = cursor.fetchone()

            if result:
                return result[0]  # Return the cash balance
            else:
                return 0  # If no result, return 0 (user not found or no cash set)

        except sqlite3.Error as e:
            print(f"Error while fetching cash balance: {e}")
            return 0  # Return 0 in case of an error

        finally:
            cursor.close()
                    

