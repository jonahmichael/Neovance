#!/bin/bash
# Neovance-AI Complete Application Status & Access Guide
# Run this script to check all services and get access information

echo "🌟 NEOVANCE-AI APPLICATION STATUS"
echo "======================================="
echo ""

# Check service status
echo "🔍 Service Health Check:"
echo "------------------------"

# Backend API
backend_status=$(curl -s http://localhost:8000/ 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "❌ Not running")
echo "✅ Backend API: $backend_status"

# ML Prediction Service  
ml_status=$(curl -s http://localhost:8001/health 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "❌ Not running")
echo "✅ ML Service: $ml_status"

# Frontend check
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ Frontend: Running on port 3000"
elif curl -s http://localhost:3006 >/dev/null 2>&1; then
    echo "✅ Frontend: Running on port 3006"
else
    echo "❌ Frontend: Not running"
fi

echo ""
echo "🌐 ACCESS YOUR APPLICATION:"
echo "============================"
echo "📊 Backend API & Data: http://localhost:8000"
echo "📋 Backend Documentation: http://localhost:8000/docs"
echo "🧠 ML Prediction API: http://localhost:8001"  
echo "🔬 ML API Documentation: http://localhost:8001/docs"
echo "🖥️ Frontend Dashboard: http://localhost:3000 (or 3006)"
echo ""

# Show sample data
echo "👥 Current NICU Patients:"
echo "------------------------"
babies=$(curl -s http://localhost:8000/babies 2>/dev/null | grep -o '"mrn":"[^"]*"' | head -5)
if [ -n "$babies" ]; then
    echo "$babies" | cut -d'"' -f4 | nl
else
    echo "No patients data available"
fi

echo ""
echo "🧪 FUNCTIONALITY TESTING:"
echo "=========================="
echo "1. 🔬 Test Model Only: python test_your_model.py"
echo "2. 🧪 Quick All Tests: python quick_model_test.py" 
echo "3. 🔄 Test HIL Workflow: python test_complete_hil_workflow.py"
echo "4. ⚡ One-Click System: python run_ml_hil_system.py"
echo ""

echo "📋 APPLICATION FEATURES:"
echo "========================"
echo "✅ NICU Patient Management"
echo "✅ Real-time Vital Signs Monitoring"
echo "✅ Sepsis Risk Prediction (ML)"
echo "✅ EOS Risk Calculator"  
echo "✅ Clinical Decision Support"
echo "✅ Human-in-the-Loop Learning"
echo "✅ Live Data Simulation"
echo "✅ Interactive Dashboard"
echo ""

echo "🔧 TROUBLESHOOTING:"
echo "==================="
echo "• Port conflicts? Check: netstat -tlnp | grep ':800[01]'"
echo "• Model issues? Run: python test_your_model.py"
echo "• Frontend not loading? Check: npm run dev in frontend/dashboard/"
echo "• Database issues? Run: python backend/check_db.py"
echo ""

echo "🎯 NEXT STEPS:"
echo "=============="
echo "1. Open http://localhost:8000/docs - Explore Backend API"
echo "2. Open http://localhost:8001/docs - Test ML Predictions"
echo "3. Open http://localhost:3000 - Use Dashboard Interface"
echo "4. Run python test_your_model.py - Verify ML Model"
echo "5. View actual baby data at /babies endpoint"