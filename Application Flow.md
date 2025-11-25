
The application onces started from docker compose starts the DB service and broker service 

There are 2 main components of the application
1. Web Application - exposes REST API to create notification requests and view id
2. Consumer Application - picks up the notification requests from the broker and process them to send notifications

There are other services like the DB viewer and Kafka UI to view the DB and Kafka topics respectively.

## Application Flow
1. User sends a POST request to the Web Application to create a notification.
2. The Web Application validates the request and stores the notification request in the topics in the broker (Kafka).
3. if the request is for scheduling the notification for later time, the request is stored with the scheduled time. 
4. The Consumer Application listens to the topics in the broker and picks up the notification requests.
5. The Consumer Application processes the notification requests and sends notifications via the specified channels (email, slack, in-app).
6. The status of the notification (sent, failed, pending) is updated in the database by the consumer 

