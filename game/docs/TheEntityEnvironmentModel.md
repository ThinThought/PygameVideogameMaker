# The Entity-Environment-Interaction Model

This model currently uses two basic constructs to build a videogame system: `Environment` and `Entity`.

The principles are simple and follow object-oriented programming:

## Environment

Represents spaces. An environment can have properties or declare rules that are applied directly to its child entities.

- There is a Void Environment that has no rules affecting child entities.
- An environment can exist on its own or be created as a child of an entity.
- An environment can combine characteristics from other environments within the entity it inhabits.
- Environments interact by combining their characteristics. The sum of properties from one or more environments is applied individually to the child entities of each environment.

## Entity

Represents interactive objects within an environment (characters, items, obstacles, etc.).

An entity can be given any variable or component that enables interaction with its parent environment.

- An entity is always born inside an Environment.
- An entity can itself contain environments, enabling the creation of additional entities.
