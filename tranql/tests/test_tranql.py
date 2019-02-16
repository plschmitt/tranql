import json
import pytest
from tranql.main import TranQL
from tranql.ast import SetStatement
from tranql.tests.mocks import mock_icees_wf5_mod_1_4_response
from tranql.tests.mocks import mock_graph_gamma_quick

def assert_lists_equal (a, b):
    assert len(a) == len(b)
    for index, element in enumerate(a):
        actual = b[index]
        assert len(element) == len(actual)
        for s_index, s in enumerate(element):
            print (f"  --assert: actual: {actual[s_index]} s: {s}")
            assert actual[s_index] == s

def assert_parse_tree (code, expected):
    tranql = TranQL ()
    assert_lists_equal (
        tranql.parser.parse (code).parse_tree,
        expected)
    
#####################################################
#
# Parser tests. Verify we produce the AST for the
# expected grammar correctly.
#
#####################################################

def test_parse_set ():
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

def test_parse_set_with_comment ():
    """ Test parsing set statements with comments. """
    print (f"test_parse_set_with_comment()")
    assert_parse_tree (
        code = """
        -- This is a comment
        SET disease = 'asthma' """,
        expected = [
            ["set", "disease", "=", "asthma"]
        ])

def test_parse_select_simple ():
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
    
def test_parse_select_complex ():
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
    
#####################################################
#
# AST tests. Test abstract syntax tree components.
#
#####################################################
def test_ast_set_variable ():
    """ Test setting a varaible to an explicit value. """
    tranql = TranQL ()
    statement = SetStatement (variable="variable", value="x")
    statement.execute (tranql)
    assert tranql.context.resolve_arg ("$variable") == 'x'
def test_ast_set_graph ():
    """ Set a variable to a graph passed as a result. """
    tranql = TranQL ()
    statement = SetStatement (variable="variable", value=None, jsonpath_query=None)
    statement.execute (tranql, context={ 'result' : { "a" : 1 } })
    assert tranql.context.resolve_arg ("$variable")['a'] == 1
def test_ast_set_graph ():
    """ Set a variable to the value returned by executing a JSONPath query. """
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
'''
def test_ast_select_simple (requests_mock):
    requests_mock.get("http://localhost:8099/flow/5/mod_1_4/icees/by_residential_density",
                      text=mock_icees_wf5_mod_1_4_response)
    requests_mock.get("http://localhost:8099/graph/gamma/quick",
                      text=mock_graph_gamma_quick)
'''

#####################################################
#
# Interpreter tests. Test the interpreter interface.
#
#####################################################
def test_interpreter_set ():
    """ Test set statements by executing a few and checking values after. """
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
    print (f"resolved variables --> {json.dumps(output, indent=2)}")
    assert output['disease'] == "asthma"
    assert output['cohort'] == "COHORT:22"

def test_program (requests_mock):
    requests_mock.post (
        "http://localhost:8099/flow/5/mod_1_4/icees/by_residential_density",
        text=json.dumps (mock_icees_wf5_mod_1_4_response, indent=2))
    requests_mock.post (
        "http://localhost:8099/graph/gamma/quick",
        text=json.dumps (mock_graph_gamma_quick, indent=2))

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
    
    SELECT disease->chemical_substance
      FROM "/flow/5/mod_1_4/icees/by_residential_density"
     WHERE disease = "asthma"
       AND EstResidentialDensity < "2"
       AND cohort = "COHORT:22"
       AND max_p_value = "0.5"
       SET '$.nodes.[*].id' AS chemical_exposures
    
    SELECT chemical_substance->gene->biological_process->phenotypic_feature
      FROM "/graph/gamma/quick"
     WHERE chemical_substance = $chemical_exposures
       SET knowledge_graph
    """)
    
    print (f"{ast}")
    expos = tranql.context.resolve_arg("$chemical_exposures")
    print (f" expos =======> {json.dumps(expos)}")
    
    kg = tranql.context.resolve_arg("$knowledge_graph")
    print (f" kg =======> {json.dumps(kg)}")

def test_program_variables (requests_mock):
    requests_mock.post (
        "http://localhost:8099/flow/5/mod_1_4/icees/by_residential_density",
        text=json.dumps (mock_icees_wf5_mod_1_4_response, indent=2))
    requests_mock.post (
        "http://localhost:8099/graph/gamma/quick",
        text=json.dumps (mock_graph_gamma_quick, indent=2))

    tranql = TranQL ()
    ast = tranql.execute ("""
    --
    -- Workflow 5
    --
    --   Modules 1-4: Chemical Exposures by Clinical Clusters
    --      For sub-clusters within the overall ICEES asthma cohort defined by
    --      differential population density, which chemicals are related to these clusters
    --      with a p_value less than some threshold?
    --
    --   Modules 5-*: Knowledge Graph Phenotypic Associations 
    --      For chemicals produced by the first steps, what phenotypes are associated with exposure
    --      to these chemicals?
    --
    
    SET disease = "asthma"
    SET max_p_value = '0.5'
    SET cohort = 'COHORT:22'
    SET population_density = 2
    SET icees.population_density_cluster = '/wf5/mod_1_4/icees/by_residential_density'
    SET gamma.quick = '/graph/gamma/quick/'
    
    SELECT disease->chemical_substance
      FROM $icees.population_density_cluster
     WHERE disease = $disease
       AND population_density < $population_density
       AND cohort = $cohort
       AND max_p_value = $max_p_value
       SET '$.nodes.[*]' AS exposures
    
    SELECT chemical_substance->gene->biological_process->phenotypic_feature
      FROM $gamma.quick
     WHERE chemical_substance = $exposures
       SET knowledge_graph
    """ )
    

