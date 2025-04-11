import pytest
from unittest.mock import patch
from script_py.argocd_client import ArgoCDClient

@patch("script_py.argocd_client.requests.get")
def test_get_applications(mock_get):
    """
    Test the get_applications method of ArgoCDClient.
    This test mocks the requests.get method to simulate a successful response from the ArgoCD API.
    """
    # Simular una respuesta exitosa de la API de ArgoCD
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"items": [{"metadata": {"name": "app-1"}}]}

    # Llamar al método que se está probando
    apps = ArgoCDClient.get_applications()

    # Verificar que el resultado sea el esperado
    assert len(apps) == 1
    assert apps[0]["metadata"]["name"] == "app-1"

    # Verificar que se haya llamado a la API con la URL correcta
    mock_get.assert_called_once_with(
        f"{ArgoCDClient.Config.ARGOCD_API}/applications",
        headers={"Authorization": f"Bearer {ArgoCDClient.Config.ARGOCD_TOKEN}"},
        verify=False,
        timeout=10
    )
