db.createUser({
    user: "vyeso",
    pwd: "qweqwe000",
    roles: [{ role: "readWrite", db: "sensor_db" }]
});

db = db.getSiblingDB('sensor_db'); // Use the correct database name

// Create a collection (MongoDB doesn't have schemas like SQL)
db.createCollection('sensor_data');

