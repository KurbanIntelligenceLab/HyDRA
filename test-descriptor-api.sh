#!/bin/bash

# Test DescriptorDashboard API endpoints

echo "======================================"
echo "Testing DescriptorDashboard API"
echo "======================================"
echo ""

PROJECT="zr-tio2"
BASE_URL="http://localhost:8000"

echo "1. Testing /api/data/$PROJECT/descriptors"
echo "--------------------------------------"
curl -s "$BASE_URL/api/data/$PROJECT/descriptors" | jq '{ columns: .columns, num_systems: .summary.num_systems, num_descriptors: .summary.num_descriptors }' || echo "FAILED"
echo ""

echo "2. Testing /api/data/$PROJECT/correlation"
echo "--------------------------------------"
curl -s "$BASE_URL/api/data/$PROJECT/correlation" | jq '{ num_columns: (.columns | length), matrix_size: (.matrix | length) }' || echo "FAILED"
echo ""

echo "3. Testing /api/data/$PROJECT/shifts"
echo "--------------------------------------"
curl -s "$BASE_URL/api/data/$PROJECT/shifts" | jq '{ pairs_found, num_descriptors: (.descriptors | length) }' || echo "FAILED"
echo ""

echo "======================================"
echo "✅ If you see JSON output above, the API is working!"
echo "❌ If you see 'FAILED', check if backend is running:"
echo "    cd /Users/jp/zroAgents"
echo "    uvicorn backend.main:app --reload --port 8000"
echo "======================================"
