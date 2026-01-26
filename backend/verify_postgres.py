#!/usr/bin/env python3

"""
Simple PostgreSQL verification script for Neovance HIL system
"""

import asyncio
import asyncpg
import sys

async def verify_postgres():
    """Verify PostgreSQL connection and setup"""
    
    print("🔍 POSTGRESQL VERIFICATION")
    print("=" * 50)
    
    # Test connection parameters
    db_configs = [
        {
            "name": "Local PostgreSQL (default)",
            "host": "localhost",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": "password"
        },
        {
            "name": "Neovance Database",
            "host": "localhost", 
            "port": 5432,
            "database": "neovance_db",
            "user": "postgres",
            "password": "password"
        }
    ]
    
    for config in db_configs:
        print(f"\n📡 Testing: {config['name']}")
        print(f"   Host: {config['host']}:{config['port']}")
        print(f"   Database: {config['database']}")
        
        try:
            # Test connection
            conn_url = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
            conn = await asyncpg.connect(conn_url)
            
            # Test basic query
            result = await conn.fetchval("SELECT version()")
            print(f"   ✅ Connection successful!")
            print(f"   📋 PostgreSQL version: {result.split(',')[0]}")
            
            # Check TimescaleDB extension
            try:
                timescale_result = await conn.fetchval(
                    "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
                )
                if timescale_result:
                    print(f"   🚀 TimescaleDB version: {timescale_result}")
                else:
                    print("   ⚠️  TimescaleDB extension not found")
            except Exception as e:
                print("   ⚠️  TimescaleDB check failed")
            
            # If this is the neovance_db, check tables
            if config['database'] == 'neovance_db':
                print("\n   📊 Checking HIL tables:")
                tables = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                expected_tables = ['alerts', 'babies', 'outcomes', 'realtime_vitals']
                found_tables = [table['table_name'] for table in tables]
                
                for table in expected_tables:
                    if table in found_tables:
                        print(f"      ✅ {table}")
                    else:
                        print(f"      ❌ {table} (missing)")
                
                # Check hypertables
                try:
                    hypertables = await conn.fetch("""
                        SELECT hypertable_name 
                        FROM timescaledb_information.hypertables
                    """)
                    
                    if hypertables:
                        print("\n   ⚡ TimescaleDB Hypertables:")
                        for ht in hypertables:
                            print(f"      ✅ {ht['hypertable_name']}")
                    else:
                        print("\n   ⚠️  No hypertables found")
                        
                except Exception as e:
                    print(f"\n   ⚠️  Hypertable check failed: {e}")
            
            await conn.close()
            
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            continue
    
    print("\n🎯 VERIFICATION SUMMARY")
    print("=" * 50)
    print("If you see connection errors, try:")
    print("1. Start PostgreSQL service: sudo systemctl start postgresql")
    print("2. Create neovance_db: createdb neovance_db")
    print("3. Run setup: python backend/setup_database.py")
    print("4. Install TimescaleDB: https://docs.timescale.com/install/")

if __name__ == "__main__":
    asyncio.run(verify_postgres())