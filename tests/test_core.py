import threading
from unittest.mock import Mock, patch
import pytest
from jarvis.core import Agent, validate

@pytest.mark.parametrize('args',[
    {'action':'shell'}, {'action':'click','x':-1,'y':0},
    {'action':'click','x':True,'y':0}, {'action':'scroll','amount':11},
    {'action':'open_url','text':'file:///C:/secret'},
    {'action':'open_url','text':'javascript:alert(1)'},
    {'action':'open_url','text':'https://user:pass@example.org'},
    {'action':'type','text':'x'*4001}, {'action':'hotkey','keys':[]},
    {'action':'screenshot','command':'evil'},
])
def test_reject_invalid_actions(args):
    with pytest.raises(ValueError): validate(args,1920,1080)

@pytest.mark.parametrize('args',[
    {'action':'click','x':1919,'y':1079},
    {'action':'type','text':'مرحبا ياسين'},
    {'action':'hotkey','keys':['ctrl','l']},
    {'action':'open_url','text':'https://example.org'},
])
def test_valid_actions(args): validate(args,1920,1080)

def response(calls):
    r = Mock(status_code=200,is_error=False)
    r.json.return_value = {'choices':[{'message':{'role':'assistant','content':None,'tool_calls':calls}}]}
    return r

def tool(action='click'):
    return {'id':'1','type':'function','function':{'name':'desktop','arguments':'{"action":"'+action+'","x":10,"y":20}'}}

@patch('jarvis.core.httpx.Client')
def test_denied_action_never_executes(client):
    desktop = Mock()
    client.return_value.__enter__.return_value.post.return_value = response([tool()])
    agent = Agent('key','openrouter/free',desktop,lambda _:False,lambda _:None,threading.Event())
    assert agent.run('click') == 'Action cancelled.'
    desktop.execute.assert_not_called()
    desktop.snapshot.assert_not_called()

@patch('jarvis.core.httpx.Client')
def test_cancel_while_approving_never_executes(client):
    stop = threading.Event(); desktop = Mock()
    client.return_value.__enter__.return_value.post.return_value = response([tool()])
    def approve(args): stop.set(); return True
    agent = Agent('key','openrouter/free',desktop,approve,lambda _:None,stop)
    assert agent.run('click') == 'Action cancelled.'
    desktop.execute.assert_not_called()

@patch('jarvis.core.httpx.Client')
def test_parallel_mutations_rejected(client):
    desktop = Mock()
    client.return_value.__enter__.return_value.post.return_value = response([tool(),tool()])
    agent = Agent('key','openrouter/free',desktop,lambda _:True,lambda _:None,threading.Event())
    with pytest.raises(RuntimeError,match='multiple'): agent.run('click')
    desktop.execute.assert_not_called()

def test_paid_model_rejected():
    with pytest.raises(ValueError): Agent('key','paid-model',None,None,None,None)

@patch('jarvis.core.httpx.Client')
def test_rate_limit_is_actionable(client):
    client.return_value.__enter__.return_value.post.return_value = Mock(status_code=429)
    agent = Agent('key','openrouter/free',Mock(),lambda _:True,lambda _:None,threading.Event())
    with pytest.raises(RuntimeError,match='rate limit'): agent.run('hello')

@patch('jarvis.core.httpx.Client')
def test_execute_then_observe(client):
    desktop = Mock(); desktop.snapshot.return_value = 'data:image/jpeg;base64,abc'
    r = Mock(status_code=200,is_error=False)
    r.json.return_value = {'choices':[{'message':{'content':'Done.'}}]}
    post = client.return_value.__enter__.return_value.post
    post.side_effect = [response([tool()]),r]
    agent = Agent('key','openrouter/free',desktop,lambda _:True,lambda _:None,threading.Event())
    assert agent.run('click') == 'Done.'
    desktop.execute.assert_called_once()
    desktop.snapshot.assert_called_once()
    assert post.call_count == 2
