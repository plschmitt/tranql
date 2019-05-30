import json
import pytest
import os
import requests
import requests_mock as r_mock
from deepdiff import DeepDiff
from tranql.main import TranQL
from tranql.main import TranQLParser, set_verbose
from tranql.tranql_ast import SetStatement
from tranql.tests.mocks import MockHelper
from tranql.tests.mocks import MockMap
#set_verbose ()

def assert_lists_equal (a, b):
    """ Assert the equality of two lists. """
    assert len(a) == len(b)
    for index, expected in enumerate(a):
        actual = b[index]
        if isinstance(actual,str) and isinstance(expected, str) and \
           actual.isspace() and expected.isspace ():
            continue
        elif isinstance(actual, list) and isinstance(expected, list):
            assert_lists_equal (actual, expected)
        else:
            assert actual == expected

def assert_parse_tree (code, expected):
    """ Parse a block of code into a parse tree. Then assert the equality
    of that parse tree to a list of expected tokens. """
    tranql = TranQL ()
    actual = tranql.parser.parse (code).parse_tree
    #print (f"{actual}")
    assert_lists_equal (
        actual,
        expected)

#####################################################
#
# Parser tests. Verify we produce the AST for the
# expected grammar correctly.
#
#####################################################

def test_parse_predicate (requests_mock):
    set_mock(requests_mock, "workflow-5")

    """ Test parsing a predicate. """
    print (f"test_parse_predicate()")
    assert_parse_tree (
        code = """
        SELECT chemical_substance-[treats]->disease
          FROM "/graph/gamma/quick"
          WHERE chemical_substance='PUBCHEM:2083'
            SET "$.knowledge_graph.nodes.[*].id as indications
        """,
        expected = [
            [ [ "select",
                "chemical_substance",
                [ "-[",
                  "treats",
                  "]->"
                ], "disease", "\n"
            ],
            "          ",
            [ "from", [ "/graph/gamma/quick"] ],
            ["where",
             [
                 "chemical_substance",
                 "=",
                 "PUBCHEM:2083"
             ]
            ], [ "" ]
            ]])

def set_mock (requests_mock, name):
    mock_map = MockMap (requests_mock, name)
    session = requests.Session()
    adapter = r_mock.Adapter()
    session.mount('requests_mock', adapter)

def test_parse_set (requests_mock):
    set_mock(requests_mock, "workflow-5")

    """ Test parsing set statements. """
    print (f"test_parse_set()")
    assert_parse_tree (
        code = """
        SET disease = 'asthma'
        SET max_p_value = '0.5'
        SET cohort = 'COHORT:22'
        SET population_density = 2
        SET icees.population_density_cluster = 'http://localhost/ICEESQuery'
        SET gamma.quick = 'http://robokop.renci.org:80/api/simple/quick/' """,
        expected = [
            ["set", "disease", "=", "asthma"],
            ["set", "max_p_value", "=", "0.5"],
            ["set", "cohort", "=", "COHORT:22"],
            ["set", "population_density", "=", 2],
            ["set", "icees.population_density_cluster", "=", "http://localhost/ICEESQuery"],
            ["set", "gamma.quick", "=", "http://robokop.renci.org:80/api/simple/quick/"]
        ])

def test_parse_set_with_comment (requests_mock):
    set_mock(requests_mock, "workflow-5")
    """ Test parsing set statements with comments. """
    print (f"test_parse_set_with_comment()")
    assert_parse_tree (
        code = """
        -- This is a comment
        SET disease = 'asthma' """,
        expected = [
            ["set", "disease", "=", "asthma"]
        ])

def test_parse_select_simple (requests_mock):
    set_mock(requests_mock, "workflow-5")
    """ Verify the token stream of a simple select statement. """
    print (f"test_parse_select_simple()")
    assert_parse_tree (
        code = """
        SELECT chemical_substance->gene->biological_process->phenotypic_feature
          FROM "/graph/gamma/quick"
         WHERE chemical_substance = $chemical_exposures
           SET knowledge_graph """,
        expected = [
            [["select", "chemical_substance", "->", "gene", "->", "biological_process", "->", "phenotypic_feature", "\n"],
             "          ",
             ["from", ["/graph/gamma/quick"]],
             ["where", ["chemical_substance", "=", "$chemical_exposures"]],
             ["set", ["knowledge_graph"]]]
        ])

def test_parse_select_complex (requests_mock):
    set_mock(requests_mock, "workflow-5")
    """ Verify the token stream of a more complex select statement. """
    print (f"test_parse_select_complex()")
    assert_parse_tree (
        code = """
        SELECT disease->chemical_substance
          FROM "/flow/5/mod_1_4/icees/by_residential_density"
         WHERE disease = "asthma"
           AND EstResidentialDensity < "2"
           AND cohort = "COHORT:22"
           AND max_p_value = "0.5"
           SET '$.nodes.[*].id' AS chemical_exposures """,
        expected = [
            [["select", "disease", "->", "chemical_substance", "\n"],
             "          ",
             ["from", ["/flow/5/mod_1_4/icees/by_residential_density"]],
             ["where",
              ["disease", "=", "asthma"], "and",
              ["EstResidentialDensity", "<", "2"], "and",
              ["cohort", "=", "COHORT:22"], "and",
              ["max_p_value", "=", "0.5"]
             ],
             ["set", ["$.nodes.[*].id", "as", "chemical_exposures"]]]
        ])

def test_parse_query_with_repeated_concept (requests_mock):
    set_mock(requests_mock, "workflow-5")
    """ Verify the parser accepts a grammar allowing concept names to be prefixed by a name
    and a colon. """
    print (f"test_parse_query_with_repeated_concept")
    assert_parse_tree (
        code="""
        SELECT cohort_diagnosis:disease->diagnoses:disease
          FROM '/clinical/cohort/disease_to_chemical_exposure'
         WHERE cohort_diagnosis = 'asthma'
           AND Sex = '0'
           AND cohort = 'all_patients'
           AND max_p_value = '0.5'
           SET '$.knowledge_graph.nodes.[*].id' AS diagnoses
        """,
        expected = [
            [["select", "cohort_diagnosis:disease","->","diagnoses:disease","\n"],
             "  ",
             ["from",
              ["/clinical/cohort/disease_to_chemical_exposure"]
             ],
             ["where",
              ["cohort_diagnosis","=","asthma"],
              "and",
              ["Sex","=","0"],
              "and",
              ["cohort","=","all_patients"],
              "and",
              ["max_p_value","=","0.5"]
             ],
             ["set",
              ["$.knowledge_graph.nodes.[*].id","as","diagnoses"]
             ]
            ]])

#####################################################
#
# AST tests. Test abstract syntax tree components.
#
#####################################################
def test_ast_set_variable (requests_mock):
    set_mock(requests_mock, "workflow-5")
    """ Test setting a varaible to an explicit value. """
    print ("test_ast_set_variable ()")
    tranql = TranQL ()
    statement = SetStatement (variable="variable", value="x")
    statement.execute (tranql)
    assert tranql.context.resolve_arg ("$variable") == 'x'
def test_ast_set_graph (requests_mock):
    set_mock(requests_mock, "workflow-5")
    """ Set a variable to a graph passed as a result. """
    print ("test_ast_set_graph ()")
    tranql = TranQL ()
    statement = SetStatement (variable="variable", value=None, jsonpath_query=None)
    statement.execute (tranql, context={ 'result' : { "a" : 1 } })
    assert tranql.context.resolve_arg ("$variable")['a'] == 1
def test_ast_set_graph (requests_mock):
    set_mock(requests_mock, "workflow-5")
    """ Set a variable to the value returned by executing a JSONPath query. """
    print ("test_ast_set_graph ()")
    tranql = TranQL ()
    statement = SetStatement (variable="variable", value=None, jsonpath_query="$.nodes.[*]")
    statement.execute (tranql, context={
        'result' : {
            "nodes" : [ {
                "id" : "x:y"
            } ]
        }
    })
    assert tranql.context.resolve_arg ("$variable")[0]['id'] == "x:y"
def test_ast_generate_questions (requests_mock):
    set_mock(requests_mock, "workflow-5")
    """ Validate that
           -- named query concepts work.
           -- the question graph is build incorporating where clause constraints.
    """
    print ("test_ast_set_generate_questions ()")
    app = TranQL ()
    ast = app.parse ("""
        SELECT cohort_diagnosis:disease->diagnoses:disease
          FROM '/clinical/cohort/disease_to_chemical_exposure'
         WHERE cohort_diagnosis = 'MONDO:0004979' --asthma
           AND Sex = '0'
           AND cohort = 'all_patients'
           AND max_p_value = '0.5'
           SET '$.knowledge_graph.nodes.[*].id' AS diagnoses
    """)
    questions = ast.statements[0].generate_questions (app)
    assert questions[0]['question_graph']['nodes'][0]['curie'] == 'MONDO:0004979'
    assert questions[0]['question_graph']['nodes'][0]['type'] == 'disease'

# def test_ast_merge_results (requests_mock):
#     set_mock(requests_mock, "workflow-5")
#     """ Validate that
#             -- Results from the query plan are being merged together correctly
#     """
#     print("test_ast_merge_answers ()")
#     tranql = TranQL ()
#     ast = tranql.parse ("""
#         SELECT cohort_diagnosis:disease->diagnoses:disease
#           FROM '/clinical/cohort/disease_to_chemical_exposure'
#          WHERE cohort_diagnosis = 'MONDO:0004979' --asthma
#            AND Sex = '0'
#            AND cohort = 'all_patients'
#            AND max_p_value = '0.5'
#            SET '$.knowledge_graph.nodes.[*].id' AS diagnoses
#     """)
#
#     select = ast.statements[0]
#
#     # What is the proper format for the name of a mock file? This should be made into one
#     mock_responses = [
#         {
#             'knowledge_graph': {
#                 'nodes': [
#                     {'id': 'CHEBI:28177', 'type': 'chemical_substance'},
#                     {'id': 'HGNC:2597', 'type': 'gene'}
#                 ],
#                 'edges': [
#                     {'id': 'e0', 'source_id': 'n0', 'target_id': 'n1'}
#                 ]
#             },
#             'knowledge_map': [
#                 {
#                     'node_bindings': {
#                         'chemical_substance': 'CHEBI:28177',
#                         'gene': 'HGNC:2597'
#                     },
#                     'edge_bindings': {
#                         'e1': [
#                             'e0'
#                         ],
#                         's0': '1cdd83d6-7f6b-4b17-9139-63f8e81f2122'
#                     },
#                     'score': 0.09722323258334348
#                 }
#             ]
#         },
#         {
#             'knowledge_graph': {
#                 'nodes': [
#                     {'id': 'CHEBI:28177', 'type': 'chemical_substance'},
#                     {'id': 'TEST:00000', 'type': 'TEST'}
#                 ],
#                 'edges': [
#                     {'id': 'e0', 'source_id': 'n0', 'target_id': 'n1'}
#                 ]
#             },
#             'knowledge_map': [
#                 {
#                     'node_bindings': {
#                         'chemical_substance': 'CHEBI:28177',
#                         'gene': 'HGNC:2597'
#                     },
#                     'edge_bindings': {
#                         'e1': [
#                             'e0'
#                         ],
#                         's0': '1cdd83d6-7f6b-4b17-9139-63f8e81f2122'
#                     },
#                     'score': 0.09722323258334348
#                 }
#             ]
#         }
#     ]
#
#     expected_result = {
#         'knowledge_graph': {
#             'nodes': [
#                 {'id': 'CHEBI:28177', 'type': 'chemical_substance'},
#                 {'id': 'HGNC:2597', 'type': 'gene'},
#                 {'id': 'TEST:00000', 'type':'TEST'}
#             ],
#             'edges': [
#                 {'id': 'e0', 'source_id': 'n0', 'target_id': 'n1'}
#             ]
#         },
#         'knowledge_map': [
#             {
#                 'node_bindings': {
#                     'chemical_substance': 'CHEBI:28177',
#                     'gene': 'HGNC:2597'
#                 },
#                 'edge_bindings': {
#                     'e1': [
#                         'e0'
#                     ],
#                     's0': '1cdd83d6-7f6b-4b17-9139-63f8e81f2122'
#                 },
#                 'score': 0.09722323258334348
#             }
#         ]
#     }
#
#     merged_results = select.merge_results (mock_responses, select.service)
#
#
#     assert(merged_results == expected_result)

def test_ast_plan_strategy (requests_mock):
    set_mock(requests_mock, "workflow-5")
    print ("test_ast_plan_strategy ()")
    tranql = TranQL ()
    ast = tranql.parse ("""
        SELECT cohort_diagnosis:disease->diagnoses:disease
          FROM '/clinical/cohort/disease_to_chemical_exposure'
         WHERE cohort_diagnosis = 'MONDO:0004979' --asthma
           AND Sex = '0'
           AND cohort = 'all_patients'
           AND max_p_value = '0.5'
           SET '$.knowledge_graph.nodes.[*].id' AS diagnoses
    """)

    select = ast.statements[0]
    plan = select.planner.plan (select.query)

    expected = [
        [
            'robokop',
            '/graph/gamma/quick',
            [
                [
                    select.query.concepts['cohort_diagnosis'],
                    select.query.arrows[0],
                    select.query.concepts[select.query.order[1]]
                ]
            ]
        ]
    ]

    assert_lists_equal(
        plan,
        expected
    )

def test_ast_plan_statements (requests_mock):
    set_mock(requests_mock, "workflow-5")
    print("test_ast_plan_statements ()")
    tranql = TranQL ()
    ast = tranql.parse ("""
        SELECT cohort_diagnosis:disease->diagnoses:disease
          FROM '/clinical/cohort/disease_to_chemical_exposure'
         WHERE cohort_diagnosis = 'MONDO:0004979' --asthma
           AND Sex = '0'
           AND cohort = 'all_patients'
           AND max_p_value = '0.5'
           SET '$.knowledge_graph.nodes.[*].id' AS diagnoses
    """)


    select = ast.statements[0]
    statements = select.plan (select.planner.plan (select.query))

    assert len(statements) == 1

    statement = statements[0]

    assert len(statement.query.concepts) == 2

    assert statement.query.concepts['cohort_diagnosis'].nodes == ["MONDO:0004979"]
    assert statement.query.concepts['diagnoses'].nodes == []
    assert statement.service == "/graph/gamma/quick"
    assert statement.where == []
    assert statement.set_statements == []


def test_ast_bidirectional_query (requests_mock):
    set_mock(requests_mock, "workflow-5")
    """ Validate that we parse and generate queries correctly for bidirectional queries. """
    print ("test_ast_bidirectional_query ()")
    app = TranQL ()
    disease_id = "MONDO:0004979"
    chemical = "PUBCHEM:2083"
    app.context.set ("drug", chemical)
    app.context.set ("disease", disease_id)
    mocker = MockHelper ()
    expectations = {
        "cop.tranql" : mocker.get_obj ("bidirectional_question.json")
    }
    queries = { os.path.join (os.path.dirname (__file__), "..", "queries", k) : v
                for k, v in expectations.items () }
    for program, expected_output in queries.items ():
        ast = app.parse_file (program)
        statement = ast.statements
        """ This uses an unfortunate degree of knowledge about the implementation,
        both of the AST, and of theq query. Consider alternatives. """
        questions = ast.statements[2].generate_questions (app)
        nodes = questions[0]['question_graph']['nodes']
        edges = questions[0]['question_graph']['edges']
        node_index = { n['id'] : i for i, n in enumerate (nodes) }
        assert nodes[-1]['curie'] == disease_id
        assert nodes[0]['curie'] == chemical
        assert node_index[edges[-1]['target_id']] == node_index[edges[-1]['source_id']] - 1

#####################################################
#
# Interpreter tests. Test the interpreter interface.
#
#####################################################
def test_interpreter_set (requests_mock):
    set_mock(requests_mock, "workflow-5")
    """ Test set statements by executing a few and checking values after. """
    print ("test_interpreter_set ()")
    tranql = TranQL ()
    tranql.execute ("""
        -- Test set statements.
        SET disease = 'asthma'
        SET max_p_value = '0.5'
        SET cohort = 'COHORT:22'
        SET population_density = 2
        SET icees.population_density_cluster = 'http://localhost/ICEESQuery'
        SET gamma.quick = 'http://robokop.renci.org:80/api/simple/quick/' """)

    variables = [ "disease", "max_p_value", "cohort", "icees.population_density_cluster", "gamma.quick" ]
    output = { k : tranql.context.resolve_arg (f"${k}") for k in variables }
    #print (f"resolved variables --> {json.dumps(output, indent=2)}")
    assert output['disease'] == "asthma"
    assert output['cohort'] == "COHORT:22"

def test_program (requests_mock):
    print ("test_program ()")
    mock_map = MockMap (requests_mock, "workflow-5")
    tranql = TranQL ()
    ast = tranql.execute ("""
    --
    -- Workflow 5
    --
    --   Modules 1-4: Chemical Exposures by Clinical Clusters
    --      For sub-clusters within the overall ICEES asthma cohort defined by
    --      differential population density, which chemicals are related to these
    --      clusters with a p_value less than some threshold?
    --
    --   Modules 5-*: Knowledge Graph Phenotypic Associations
    --      For chemicals produced by the first steps, what phenotypes are
    --      associated with exposure to these chemicals?
    --
    SET id_filters = "SCTID,rxcui,CAS,SMILES,umlscui"

    SELECT population_of_individual_organisms->drug_exposure
      FROM "/clinical/cohort/disease_to_chemical_exposure"
     WHERE EstResidentialDensity < '2'
       AND population_of_individual_organizms = 'x'
       AND cohort = 'all_patients'
       AND max_p_value = '0.1'
       SET '$.knowledge_graph.nodes.[*].id' AS chemical_exposures

    SELECT chemical_substance->gene->biological_process->phenotypic_feature
      FROM "/graph/gamma/quick"
     WHERE chemical_substance = $chemical_exposures
       SET knowledge_graph
    """)

    #print (f"{ast}")
    expos = tranql.context.resolve_arg("$chemical_exposures")
    #print (f" expos =======> {json.dumps(expos)}")

    kg = tranql.context.resolve_arg("$knowledge_graph")
    assert kg['knowledge_graph']['nodes'][0]['id'] == "CHEBI:28177"
    assert kg['knowledge_map'][0]['node_bindings']['chemical_substance'] == "CHEBI:28177"
