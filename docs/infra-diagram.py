from diagrams import Cluster, Diagram, Edge
from diagrams.custom import Custom
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.general import InternetAlt2
from diagrams.aws.compute import Lambda
from diagrams.aws.storage import S3
from diagrams.aws.management import ParameterStore
from diagrams.aws.network import ELB, ClientVpn, VPC, NATGateway, InternetGateway, Route53
from diagrams.onprem.monitoring import Splunk
from diagrams.programming.language import Bash
from diagrams.programming.flowchart import SummingJunction

graph_attr = {
    # "splines":"curved",
    "compound":"true",
    "pad": "0.2"
}

with Diagram("Registrations MI Reports and Dashboards", direction="LR", show=False, graph_attr=graph_attr):
    nhsSplunk = Splunk("NHS Splunk Cloud")

    with Cluster("Local Dev Environ", direction="TB"):
        local = Bash("Developer")
        localSplunk = Splunk("Local Splunk\nInstance")
        local >> Edge(xlabel="test") >> localSplunk

    with Cluster("AWS", direction="TB"):

        with Cluster("Common (CI)\nAccount"):
            gocd = Custom("GoCD", "./gocd.png")
            local >> Edge(xlabel="push", constraint="False") >> gocd

        with Cluster("Registrations Pre-Prod Account"):
            s3 = S3("Reports and Dashboards\nBucket")
            uploader = Lambda("Splunk Uploader")
            gocd >> Edge(xlabel="1) upload", labelcolor="#00FF00",  labelloc="b", constraint="False") >> s3
            gocd >> Edge(xlabel="2) deploy",labelcolor="#00FF00",  labelloc="b",  labelangle="0", constraint="False") >> uploader
            gocd >> Edge(xlabel="3) run",labelcolor="#00FF00",  labelloc="b",  labelangle="0", constraint="False") >> uploader
            s3 >> uploader >> nhsSplunk

    

    
