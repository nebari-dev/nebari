apiVersion: v1
kind: Config
preferences: {}
current-context: ${current_context}
clusters:
%{ for cluster in clusters ~}
- cluster:
    %{~ if cluster.certificate_authority ~}
    certificate-authority: ${cluster.certificate_authority}
    %{~ endif ~}
    %{~ if cluster.certificate_authority_data ~}
    certificate-authority-data: ${cluster.certificate_authority_data}
    %{~ endif ~}
    %{~ if cluster.server ~}
    server: ${cluster.server}
    %{~ endif ~}
  name: ${cluster.name}
%{~ endfor }
contexts:
%{ for context in contexts ~}
- context:
    %{~ if context.cluster_name ~}
    cluster: ${context.cluster_name}
    %{~ endif ~}
    %{~ if context.namespace ~}
    namespace: ${context.namespace}
    %{~ endif ~}
    %{~ if context.user ~}
    user: ${context.user}
    %{~ endif ~}
  name: ${context.name}
%{~ endfor }
users:
%{ for user in users ~}
- name: ${user.name}
  user:
    %{~ if user.username ~}
    username: ${user.username}
    %{~ endif ~}
    %{~ if user.password  ~}
    password: ${user.password}
    %{~ endif ~}
    %{~ if user.token  ~}
    token: ${user.token}
    %{~ endif ~}
    %{~ if user.client_certificate  ~}
    client-certificate: ${user.client_certificate}
    %{~ endif ~}
    %{~ if user.client_key  ~}
    client-key: ${user.client_key}
    %{~ endif ~}
    %{~ if user.client_certificate_data  ~}
    client-certificate-data: ${user.client_certificate_data}
    %{~ endif ~}
    %{~ if user.client_key_data  ~}
    client-key-data: ${user.client_key_data}
    %{~ endif ~}
%{~ endfor ~}