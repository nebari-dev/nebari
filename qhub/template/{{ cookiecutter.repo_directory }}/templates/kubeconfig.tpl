{
   "apiVersion" : "v1",
   "clusters" : [
     {
       "cluster" :
       {
         "certificate-authority-data": "${cluster.certificate_authority_data}",
         "server": "${cluster.server}"
       },
       "name" : "${cluster.name}"
     }
   ],
   "contexts" : [
     {
       "context" :
       {
         "cluster": "${context.cluster_name}",
         "user": "${context.user}"
       },
       "name" : "${context.name}"
     }
   ],
   "kind" : "Config",
   "preferences": "{}",
   "users" : [
     {
       "name" : "${user.name}",
       "user" : {
         "client_certificate-data": "${user.client_certificate_data}",
         "client-key-data": "${user.client_key_data}"
       }
     }
   ]
}
