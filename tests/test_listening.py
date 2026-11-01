from jarvis.listening import wake_command,Utterances

def test_wake_words():
    assert wake_command('مرحبا جارفيس') == ''
    assert wake_command('Jarvis, open browser') == 'open browser'
    assert wake_command('جارفيس افتح المتصفح') == 'افتح المتصفح'
    assert wake_command('افتح المتصفح') is None
    assert wake_command('notjarvis') is None

def test_segments_assemble_once():
    p=Utterances()
    assert p.feed({'type':'Results','is_final':False,'channel':{'alternatives':[{'transcript':'جارفيس'}]}})==''
    assert p.feed({'type':'Results','is_final':True,'channel':{'alternatives':[{'transcript':'افتح'}]}})==''
    assert p.feed({'type':'Results','is_final':True,'speech_final':True,'channel':{'alternatives':[{'transcript':'المتصفح'}]}})=='افتح المتصفح'
    assert p.feed({'type':'UtteranceEnd'})==''
