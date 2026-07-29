# Generic, French, user-facing messages for API failures — never expose str(exc) to the
# client: ApiClientError messages may originate from the backend's raw HTTP error body.
API_CONNECTION_ERROR_MESSAGE = "Le service est momentanément indisponible. Veuillez réessayer plus tard."
API_RESPONSE_ERROR_MESSAGE = "Le serveur a retourné une réponse inattendue. Veuillez réessayer."
