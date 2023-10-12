

## Overview

How everything fits together can be a bit confusing, read this section before starting to understand how local and remote projects are handled, how to sync nodes, etc. 

### Engine Code

All scientific computation code is stored in the `code/` folder within the repository. All of this code can be run using the command line application (`code/run.py`). The command line application only allows for access to local project resources and does not implicitly know the project structure. This gives a more fine grained control (running specific module tests for example) but also requires more configuration. 

The engine is comprised of two modules:

- The `cli` module in code handles accessing files, batching operations, etc. Most project level operations occur within the `cli` module. This includes making sure configurations are valid and building the model stack. 

- The `cells` module is the other component of this layer, this provides direct access to the models. 

#### Models

The models handle generating artifacts. This allows for the creation of different methods to generate the same artifact and compare the effectiveness. This section isn't meant to discuss the models in detail, each model has its own documentation. 

### Jocelyn 

Jocelyn is the ResearchFlow project that allows for models to be shared. 

