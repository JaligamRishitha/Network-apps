@echo off
echo ========================================
echo Electricity Load Request API Test
echo ========================================
echo.

echo Testing JSON Endpoint...
echo.
curl -X POST http://localhost:8000/api/integration/mulesoft/load-request ^
  -H "Content-Type: application/json" ^
  -d "{\"RequestID\":\"SF-REQ-10021\",\"CustomerID\":\"CUST-88991\",\"CurrentLoad\":5,\"RequestedLoad\":10,\"ConnectionType\":\"RESIDENTIAL\",\"City\":\"Hyderabad\",\"PinCode\":\"500081\"}"

echo.
echo.
echo ========================================
echo.
echo Testing XML Endpoint...
echo.
curl -X POST http://localhost:8000/api/integration/mulesoft/load-request/xml ^
  -H "Content-Type: application/xml" ^
  -d "<ElectricityLoadRequest><RequestID>SF-REQ-10022</RequestID><CustomerID>CUST-88992</CustomerID><CurrentLoad>10</CurrentLoad><RequestedLoad>25</RequestedLoad><ConnectionType>COMMERCIAL</ConnectionType><City>Bangalore</City><PinCode>560001</PinCode></ElectricityLoadRequest>"

echo.
echo.
echo ========================================
echo Test Complete!
echo ========================================
pause
