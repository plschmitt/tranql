# TranQL

TranQL is a query language for interactive exploration of federated graph oriented data sources.

## Background

Previous [work](https://github.com/NCATS-Tangerine/ros) focused on a workflow language for automating queries. We've also prototyped similar workflows using the [Common Workflow Language (CWL)](https://www.commonwl.org/).

Workflow languages generally provide capabilities to support large scale, fault tolerant, reproducible, automated computing. These are critical features where processes that have been refined by teams over time must be automated and shared. Common characteristics of these systems include:
  * The ability to **manage multiple, interacting, long running** third party programs (eg, genomic sequence alignment)
  * Infrastructure level support for **reproducibility** via highly technical artifacts like Docker containers.
  * **Complex syntax** in formats like YAML, which are generally unfamilar to clinical data and medical experts.

While these features are essential for some applications, they are neither targeted at nor well suited to
  * **Iterative, interactive exploration** of large data sets.
  * **Accessibility** to communities like clinical data specialists and medical experts.
  * **A programmatic interface between applications** and a data source.
  
## Interactive Exploration

The ability to explore large data sets with queries is extremely familiar to clinical data experts and many medical informatics specialists. To make semantic databases more accessible to these communities, we designed TranQL to share structural and syntactic similarities to familiar languages able to interact with distributed data sets.

In particular, the [Structured Query Language (SQL)](https://en.wikipedia.org/wiki/SQL) is among the most pervasive data query languages in use. It is vital to the work of clinical data specialists. TranQL borrows concepts from SQL while borrowing elements of graph semantics from query languages like [Cypher](https://neo4j.com/developer/cypher-query-language/).

## Design Overview

### Language

TranQL is a classic interpreter with a lexical analyzer & parser which produces token stream. The tokens are interpreted to build an abstract syntax tree modeling the program's constructs which are then executed sequentially. It supports three statement types:
  * **SET**: Assign a value to a variable.
    - ```
       SET <variable> = <value>
      ```
  * **SELECT**: Select a graph described by a pattern from a service, given various constraints. Graphs patterns are expressed using concepts from the biolink-model.
    - ```
       SELECT <graph> 
       FROM <service> 
       [WHERE <constraint> [AND <constraint]*]
       [[SET <jsonpath> AS <var> | [SET <var>]]*```
  * **CREATE GRAPH**: Create a graph at a service.
    - ```
       CREATE GRAPH <var> AT <service> AS <name>
      ```

## Standard API

The [Translator standard graph API](https://github.com/NCATS-Gamma/NCATS-ReasonerStdAPI) is a protocol for exchanging graphs with federated data sources. TranQL works with endpoints supporting this standard.

## Backplane
 
The TranQL Backplane is a collection of endpoints supporting the standard API which implement reusable question answering services, or modules. Backplane modules support a simplified syntax in the language for greater readability.

## Example

#### The Comment

The example program begins with a multi-line comment describing its intent:

![image](https://user-images.githubusercontent.com/306971/52903897-53d7a980-31f2-11e9-8d43-538ee2d44ad3.png)

#### The First Select Statement

The first statement selects a graph pattern connecting disease nodes to chemical substances, both `biolink-model` concepts.

![image](https://user-images.githubusercontent.com/306971/52904001-9d74c400-31f3-11e9-8ea9-9362de79523b.png)

The from clause specifies the path to a Backplane endpoint. Because it begins with a "/", TranQL prepends the protocol, host, and port of a configured TranQL Backplane service. The service can be any endpoint implementing the standard graph endpoint interface.

The first `where` constraint parameterizes the disease question node sent to the service. In this case, it resolves an English word into ontology identifiers using the [bionames](https://bionames.renci.org/apidocs/) API. If curies are supplied, those are used directly.

The rest of the constraints, because they do not map to graph query elements, are transmitted to the service as `options` in the standard protocol. The service being invoked validates and interprets the options. In the case above, the endpoint passes the options along to define a cohort in the ICEES clinical reasoner.

The final part of the select statement is a `set` statement which uses a JSONPath query to extract chemical identifiers from the result, store them as a variable.

#### The Second Select Statement

The second `select` statement sends a different graph query to the Gamma reasoner and parameterizes the chemical_substance concept with identifiers from the first clinical step.

![image](https://user-images.githubusercontent.com/306971/52903985-7ddd9b80-31f3-11e9-9caf-ebcf96f84fc0.png)

The resulting graph is saved as a variable.

#### Publishing to Visualizers

The Backplane implements two standard API endpoint for publishing the graph for visualization. One supports the UCSD NDEx network sharing platform and the other supports Gamma's answer visualisation facility.

![image](https://user-images.githubusercontent.com/306971/52903927-b9c43100-31f2-11e9-992e-11161e438a8b.png)

The program ends by publishing the answer set to both services.

## Status

TranQL is brand new and strictly alpha. 

## Installation and Usage

### Install:
```
git clone <repository>
cd tranql
```
### Test
```
bin/test --capture=no
```
### Run
```
bin/run tranql/workflows/workflow-5.tranql
```

## Next

  * [Done] Move to the latest standard API version (0.9.0)
  * [Done] Implement basic NDEx visualization connectivity
  * [Done] Implement basic Gamma visualization connectivity
  * Handle mappings from the standard API
  * Model queries with predicates
  * Validate queries against the biolink-model
  * Add export to and possible integration with Neo4J
  
