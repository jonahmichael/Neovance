#!/usr/bin/env python3

"""
PostgreSQL/TimescaleDB Setup Script for Neovance HIL System
This script initializes the database and creates all required tables
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from database import DatabaseConfig, init_database, check_database_health

class DatabaseSetup:
    def __init__(self):
        self.config = DatabaseConfig()
        
    async def create_database_if_not_exists(self):
        """Create the neovance_db database if it doesn't exist"""
        try:
            # Connect to default postgres database
            default_url = f"postgresql://{self.config.DB_USER}:{self.config.DB_PASSWORD}@{self.config.DB_HOST}:{self.config.DB_PORT}/postgres"
            conn = await asyncpg.connect(default_url)
            
            # Check if database exists
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.config.DB_NAME
            )
            
            if not result:
                print(f"Creating database '{self.config.DB_NAME}'...")
                await conn.execute(f'CREATE DATABASE "{self.config.DB_NAME}"')
                print(f"✓ Database '{self.config.DB_NAME}' created successfully")
            else:
                print(f"✓ Database '{self.config.DB_NAME}' already exists")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"✗ Failed to create database: {e}")
            return False
    
    async def setup_timescaledb_extension(self):
        """Enable TimescaleDB extension"""
        try:
            conn = await asyncpg.connect(self.config.ASYNC_DATABASE_URL.replace("+asyncpg", ""))
            
            # Enable TimescaleDB extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
            print("✓ TimescaleDB extension enabled")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"✗ Failed to setup TimescaleDB: {e}")
            print("Note: Make sure TimescaleDB is installed on your PostgreSQL instance")
            return False
    
    async def run_schema_sql(self):
        """Execute the schema.sql file to create tables"""
        try:
            schema_file = Path(__file__).parent / "schema.sql"
            
            if not schema_file.exists():
                print(f"✗ Schema file not found: {schema_file}")
                return False
            
            conn = await asyncpg.connect(self.config.ASYNC_DATABASE_URL.replace("+asyncpg", ""))
            
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.strip():
                    try:
                        await conn.execute(statement)
                    except Exception as e:
                        # Some statements might fail if already executed (like CREATE EXTENSION)
                        if "already exists" not in str(e).lower():
                            print(f"Warning: {e}")
            
            print("✓ Database schema created successfully")
            await conn.close()
            return True
            
        except Exception as e:
            print(f"✗ Failed to create schema: {e}")
            return False
    
    async def create_hypertables(self):
        """Create TimescaleDB hypertables"""
        try:
            conn = await asyncpg.connect(self.config.ASYNC_DATABASE_URL.replace("+asyncpg", ""))
            
            # Create hypertables
            hypertables = [
                ("alerts", "timestamp"),
                ("realtime_vitals", "timestamp")
            ]
            
            for table_name, time_column in hypertables:
                try:
                    await conn.execute(
                        f"SELECT create_hypertable('{table_name}', '{time_column}', if_not_exists => TRUE)"
                    )
                    print(f"✓ Created hypertable: {table_name}")
                except Exception as e:
                    if "already a hypertable" in str(e).lower():
                        print(f"✓ Hypertable {table_name} already exists")
                    else:
                        print(f"✗ Failed to create hypertable {table_name}: {e}")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"✗ Failed to create hypertables: {e}")
            return False
    
    async def verify_setup(self):
        """Verify the complete setup"""
        print("\n=== Verifying Database Setup ===")
        
        health_check = await check_database_health()
        
        if health_check["database_connected"]:
            print("✓ Database connection successful")
            
            if health_check["timescaledb_enabled"]:
                print("✓ TimescaleDB extension enabled")
            else:
                print("✗ TimescaleDB extension not found")
            
            # Check tables
            try:
                conn = await asyncpg.connect(self.config.ASYNC_DATABASE_URL.replace("+asyncpg", ""))
                
                tables = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
                
                table_names = [table['table_name'] for table in tables]
                expected_tables = ['alerts', 'outcomes', 'realtime_vitals', 'babies']
                
                for table in expected_tables:
                    if table in table_names:
                        print(f"✓ Table '{table}' created")
                    else:
                        print(f"✗ Table '{table}' missing")
                
                # Check hypertables
                hypertables = await conn.fetch("""
                    SELECT hypertable_name 
                    FROM timescaledb_information.hypertables
                """)
                
                hypertable_names = [ht['hypertable_name'] for ht in hypertables]
                expected_hypertables = ['alerts', 'realtime_vitals']
                
                for hypertable in expected_hypertables:
                    if hypertable in hypertable_names:
                        print(f"✓ Hypertable '{hypertable}' created")
                    else:
                        print(f"✗ Hypertable '{hypertable}' missing")
                
                await conn.close()
                
            except Exception as e:
                print(f"✗ Verification failed: {e}")
                return False
        else:
            print(f"✗ Database connection failed: {health_check.get('error', 'Unknown error')}")
            return False
        
        return True

async def main():
    """Main setup function"""
    print("🏥 NEOVANCE AI - HIL SYSTEM DATABASE SETUP")
    print("==========================================")
    print("Setting up PostgreSQL + TimescaleDB for Human-in-the-Loop learning")
    print()
    
    setup = DatabaseSetup()
    
    # Step 1: Create database
    print("=== Step 1: Database Creation ===")
    if not await setup.create_database_if_not_exists():
        print("❌ Database setup failed")
        return
    print()
    
    # Step 2: Enable TimescaleDB
    print("=== Step 2: TimescaleDB Setup ===")
    if not await setup.setup_timescaledb_extension():
        print("❌ TimescaleDB setup failed")
        return
    print()
    
    # Step 3: Create schema
    print("=== Step 3: Schema Creation ===")
    if not await setup.run_schema_sql():
        print("❌ Schema creation failed")
        return
    print()
    
    # Step 4: Create hypertables
    print("=== Step 4: Hypertable Creation ===")
    if not await setup.create_hypertables():
        print("❌ Hypertable creation failed")
        return
    print()
    
    # Step 5: Verify setup
    if await setup.verify_setup():
        print("\n🎉 HIL Database Setup Complete!")
        print()
        print("Next steps:")
        print("1. Update your environment variables:")
        print(f"   export DB_HOST={setup.config.DB_HOST}")
        print(f"   export DB_PORT={setup.config.DB_PORT}")
        print(f"   export DB_NAME={setup.config.DB_NAME}")
        print(f"   export DB_USER={setup.config.DB_USER}")
        print(f"   export DB_PASSWORD={setup.config.DB_PASSWORD}")
        print()
        print("2. Start the new HIL-enabled backend:")
        print("   python backend/main_hil.py")
        print()
        print("3. Run the PostgreSQL ETL pipeline:")
        print("   python backend/pathway_etl_postgresql.py")
    else:
        print("\n❌ Setup verification failed")
        print("Please check the errors above and try again")

if __name__ == "__main__":
    asyncio.run(main())