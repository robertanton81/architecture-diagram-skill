# C4 Model Reference

The C4 model describes software architecture at four levels of abstraction.

## Levels

| Level | Name | What it shows | Element types |
|---|---|---|---|
| C1 | System Context | The system as a black box + external actors/systems | Person, System, System_Ext |
| C2 | Container | Inside the system: deployable units (apps, databases, queues) | Container, ContainerDb, ContainerQueue |
| C3 | Component | Inside a container: major structural building blocks | Component |
| C4 | Code | Inside a component: classes, interfaces | (Rarely diagrammed) |

## When to use each level

- **C1 System Context**: Best starting point. Shows who uses the system and what external systems it depends on. Use when explaining the system to non-technical stakeholders or establishing scope.
- **C2 Container**: Most common level for technical architecture. Shows the major deployable pieces and how they communicate. Use for infrastructure planning, team organization, or onboarding.
- **C3 Component**: Inside a specific container. Use when detailing a particular service's internal structure (e.g. the modules inside the API server).
- **C4 Code**: Rarely worth creating manually — IDE class diagrams serve this purpose.

## Element types

| Element | Description | Used at |
|---|---|---|
| Person/Actor | A user or role that interacts with the system | C1, C2, C3 |
| System | A top-level software system | C1 |
| Container | A deployable unit (app, service, database, queue, file system) | C2 |
| Component | A structural building block inside a container | C3 |
| Boundary/Group | A visual grouping (system boundary, container boundary) | All levels |

## Relationships

Relationships are directed arrows between elements with a label describing the interaction:
- **Label**: verb phrase (e.g. "Sends requests to", "Reads data from", "Publishes events to")
- **Technology**: optional protocol/technology annotation (e.g. "HTTPS/JSON", "SQL", "gRPC", "AMQP")
- **Direction**: usually one-way; use bidirectional only when both directions are equally important

## Mapping codebase to C4

| Codebase artifact | Typical C4 element |
|---|---|
| Web frontend (React, Vue, Angular) | Container |
| API server (Express, FastAPI, Spring) | Container |
| Database (PostgreSQL, MongoDB, Redis) | Container (database) |
| Message queue (Kafka, RabbitMQ, SQS) | Container (queue) |
| Background worker / cron job | Container |
| Shared library / SDK | Component (or Container if deployed) |
| External SaaS (Stripe, AWS S3, Auth0) | External System |
| End user / admin | Person |
