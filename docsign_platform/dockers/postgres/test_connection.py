import psycopg2

# --- IMPORTANT ---
# Replace the placeholder text below with the actual password you saved in Step 2.
DB_PASSWORD = "YOUR_SUPER_SECRET_PASSWORD"

print("Attempting to connect to local PostgreSQL server...")

try:
    # This connection string connects to the database running on your localhost.
    conn = psycopg2.connect(
        host="192.168.10.110",
        port="5432",
        user="postgres",
        dbname="postgres",
        password=DB_PASSWORD
    )

    cursor = conn.cursor()

    # Execute a simple query to get the PostgreSQL version.
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()

    print("\n✅ Connection Successful!")
    print(f"   PostgreSQL Version: {db_version[0]}")

    # Close the connection
    cursor.close()
    conn.close()

except psycopg2.OperationalError as e:
    print("\n❌ Connection Failed. Check the following:")
    print("   1. Is the Docker container running and healthy? (Check with 'docker compose ps')")
    print("   2. Did you replace 'YOUR_SAVED_PASSWORD_HERE' with your actual password?")
    print(f"   Error details: {e}")
except Exception as e:
    print(f"\n❌ An unexpected error occurred: {e}")
