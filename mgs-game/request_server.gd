extends Node2D

@onready var http_request = $HTTPRequest

func _ready():
	print("start process")
	http_request.request_completed.connect(_on_request_completed)
	
	# URL of the server
	var url = "http://127.0.0.1:8000/ask"
	var headers = ['Content-Type: application/json']
	var input = {
		"words": ["king", "sword"],
		"topk": 5
	}
	var body = JSON.stringify(input)
	var error = http_request.request(url, headers, HTTPClient.METHOD_POST, body)
	if error != OK:
		print("Request filed: ", error)

func _on_request_completed(result, response_code, headers, body):
	print("body:", body)
	var text = body.get_string_from_utf8()
	print("text:", text)
	var data = JSON.parse_string(text)

	if typeof(data) == TYPE_DICTIONARY:
		if data.has("chosen") and data.has("candidates"):
			print("Candidates from embedding model:")
			for candidate in data["candidates"]:
				print("- %s (score: %f)" % [candidate["word"], candidate["score"]])
			print("GPT chosen word: %s" % data["chosen"])
		elif data.has("error"):
			print("Error: ", data["error"])
		else:
			print("Unexpected JSON: ", text)
	else:
		print("Invalid response: ", text)
