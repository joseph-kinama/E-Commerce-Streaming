import dotenv from "dotenv";

dotenv.config({ path: ".env" });

const configs = {
	kafka_topic_broker: process.env["KAFKA_TOPIC_BROKER"],
	kafka_user_topic: process.env["KAFKA_USER_TOPIC"],
	kafka_cosumer_group: process.env["KAFKA_CONSUMER_GROUP"],
	kafka_consumer_topic: process.env["KAFKA_CONSUMER_TOPIC"],
	kafka_consumer_client: process.env["CLIENT_ID"],
	mongodb_url: process.env["MONGODB_URL_DOCKER"] || process.env["MONGODB_URL"],
	jwt_secret: process.env["JWT_SECRET_KEY"],
};

export default configs;
