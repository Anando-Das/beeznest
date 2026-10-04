import MySQLdb

try:
    db = MySQLdb.connect(host="127.0.0.1", port=3306, user="root", passwd="")
    cursor = db.cursor()
    
    # Repair table if needed
    cursor.execute("REPAIR TABLE mysql.db;")
    print("Repaired mysql.db")

    # Create the database
    cursor.execute("CREATE DATABASE IF NOT EXISTS restocrm_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print("Database restocrm_db created or already exists.")
    
    # Create the user and grant privileges
    cursor.execute("CREATE USER IF NOT EXISTS 'restocrm_user'@'localhost' IDENTIFIED BY 'secure_restocrm_pass';")
    cursor.execute("GRANT ALL PRIVILEGES ON restocrm_db.* TO 'restocrm_user'@'localhost';")
    cursor.execute("FLUSH PRIVILEGES;")
    print("User restocrm_user created and privileges granted.")
    
    db.close()
except Exception as e:
    print("Error:", e)
