#! /bin/bash

# Small script for testing endpoints. Every endpoint will return an XML or JSON response.

declare -a endpoints=( "agencyList"
		"routeList/sf-muni"
		"routeConfig/sf-muni/E"
		"predictByStopId/sf-muni/15184"
		"predictByStop/sf-muni/E/5184"
		"predictionsForMultiStops/sf-muni/N|6997"
		"predictionsForMultiStops/sf-muni/N|6997/N|3909/useShortTitles"
		"schedule/agencyList/E"
		"vehicleLocations/sf-muni/E/0"
		"stats" )

for i in "${endpoints[@]}"
do
if curl -s --head  --request GET http://127.0.0.1:8003/api/v1/$i | grep "json" > /dev/null; then
echo "Endpoint "$i "is OK"
else
echo "Endpoint "$i "is NOT OK"
fi
done
