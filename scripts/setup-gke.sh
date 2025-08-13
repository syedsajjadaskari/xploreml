#!/bin/bash
# Automatic GKE Cluster Setup for XploreML
# This script creates everything needed for XploreML deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="xploreml"
CLUSTER_NAME="xploreml-cluster"
ZONE="us-central1-a"
REGION="us-central1"
MACHINE_TYPE="e2-standard-2"
NUM_NODES=2
MIN_NODES=1
MAX_NODES=3
DISK_SIZE="30GB"

# XploreML ASCII Art
echo -e "${BLUE}"
cat << "EOF"
 __  __      _                 __  __ _     
|  \/  |    | |               |  \/  | |    
| \  / |    | |     ___  _ __ | \  / | |    
| |\/| |_  _| |    / _ \| '__|| |\/| | |    
| |  | | |_| | |  | (_) | |   | |  | | |____
|_|  |_|\__,_|_|   \___/|_|   |_|  |_|______|

XploreML - Automatic GKE Cluster Setup
EOF
echo -e "${NC}"

echo -e "${GREEN}🚀 Setting up GKE cluster for XploreML...${NC}"
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "  Project ID: $PROJECT_ID"
echo -e "  Cluster Name: $CLUSTER_NAME"
echo -e "  Zone: $ZONE"
echo -e "  Machine Type: $MACHINE_TYPE"
echo -e "  Nodes: $NUM_NODES (auto-scale: $MIN_NODES-$MAX_NODES)"
echo ""

# Function to check command success
check_command() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1 failed${NC}"
        exit 1
    fi
}

# Function to wait with spinner
wait_with_spinner() {
    local pid=$1
    local delay=0.75
    local spinstr='|/-\'
    echo -n "  "
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Step 1: Set project
echo -e "${BLUE}🔧 Setting up project configuration...${NC}"
gcloud config set project $PROJECT_ID > /dev/null 2>&1
check_command "Project set to $PROJECT_ID"

# Step 2: Enable APIs
echo -e "${BLUE}🔌 Enabling required APIs...${NC}"
echo -e "${YELLOW}  This may take 2-3 minutes...${NC}"

apis=(
    "container.googleapis.com"
    "compute.googleapis.com"
    "storage.googleapis.com"
    "containerregistry.googleapis.com"
    "cloudbuild.googleapis.com"
    "logging.googleapis.com"
    "monitoring.googleapis.com"
    "iam.googleapis.com"
)

for api in "${apis[@]}"; do
    echo -n "  Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID > /dev/null 2>&1 &
    wait_with_spinner $!
    echo -e " ${GREEN}✅${NC}"
done

echo -e "${YELLOW}⏳ Waiting for APIs to fully activate (60 seconds)...${NC}"
sleep 60

# Verify APIs
echo -e "${BLUE}🔍 Verifying APIs are enabled...${NC}"
gcloud services list --enabled --project=$PROJECT_ID --filter="name:(container.googleapis.com OR compute.googleapis.com OR storage.googleapis.com)" --format="table(name)" > /dev/null 2>&1
check_command "Required APIs verified"

# Step 3: Create service account (if not exists)
echo -e "${BLUE}👤 Setting up service account...${NC}"
if ! gcloud iam service-accounts describe xploreml-sa@$PROJECT_ID.iam.gserviceaccount.com > /dev/null 2>&1; then
    echo "  Creating service account..."
    gcloud iam service-accounts create xploreml-sa \
        --project=$PROJECT_ID \
        --display-name="XploreML Service Account" \
        --description="Service account for XploreML application" > /dev/null 2>&1
    check_command "Service account created"
    
    # Add roles
    echo "  Adding IAM roles..."
    roles=(
        "roles/storage.admin"
        "roles/container.admin"
        "roles/container.developer"
        "roles/iam.serviceAccountUser"
        "roles/logging.logWriter"
        "roles/monitoring.metricWriter"
    )
    
    for role in "${roles[@]}"; do
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:xploreml-sa@$PROJECT_ID.iam.gserviceaccount.com" \
            --role="$role" > /dev/null 2>&1
    done
    check_command "IAM roles assigned"
else
    echo -e "${YELLOW}  Service account already exists${NC}"
fi

# Step 4: Create GCS buckets
echo -e "${BLUE}🪣 Setting up storage buckets...${NC}"
buckets=("xploreml-temp-storage" "xploreml-models" "xploreml-data")

for bucket in "${buckets[@]}"; do
    if ! gsutil ls gs://$bucket > /dev/null 2>&1; then
        echo "  Creating bucket: $bucket..."
        gsutil mb -p $PROJECT_ID -l $REGION gs://$bucket > /dev/null 2>&1
        
        # Set bucket permissions
        gsutil iam ch serviceAccount:xploreml-sa@$PROJECT_ID.iam.gserviceaccount.com:objectAdmin gs://$bucket > /dev/null 2>&1
        check_command "Bucket $bucket created"
    else
        echo -e "${YELLOW}  Bucket $bucket already exists${NC}"
    fi
done

# Step 5: Check if cluster exists
echo -e "${BLUE}⚓ Checking for existing cluster...${NC}"
if gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID > /dev/null 2>&1; then
    echo -e "${YELLOW}  Cluster $CLUSTER_NAME already exists${NC}"
    echo -e "${BLUE}  Getting cluster credentials...${NC}"
    gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID > /dev/null 2>&1
    check_command "Cluster credentials obtained"
else
    # Step 6: Create GKE cluster
    echo -e "${BLUE}⚓ Creating GKE cluster...${NC}"
    echo -e "${YELLOW}  This will take 5-10 minutes...${NC}"
    
    gcloud container clusters create $CLUSTER_NAME \
        --project=$PROJECT_ID \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --num-nodes=$NUM_NODES \
        --disk-size=$DISK_SIZE \
        --enable-autoscaling \
        --min-nodes=$MIN_NODES \
        --max-nodes=$MAX_NODES \
        --enable-autorepair \
        --enable-autoupgrade \
        --enable-network-policy \
        --enable-ip-alias \
        --enable-shielded-nodes \
        --shielded-secure-boot \
        --shielded-integrity-monitoring \
        --enable-cloud-logging \
        --enable-cloud-monitoring \
        --addons=HorizontalPodAutoscaling,HttpLoadBalancing,NetworkPolicy \
        --service-account=xploreml-sa@$PROJECT_ID.iam.gserviceaccount.com \
        --node-labels=app=xploreml,environment=production \
        --node-taints= \
        --metadata disable-legacy-endpoints=true \
        --max-pods-per-node=64 \
        --enable-network-policy \
        --cluster-version=latest > /dev/null 2>&1
    
    check_command "GKE cluster created successfully"
    
    # Get cluster credentials
    echo -e "${BLUE}🔑 Getting cluster credentials...${NC}"
    gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID > /dev/null 2>&1
    check_command "Cluster credentials configured"
fi

# Step 7: Verify cluster is ready
echo -e "${BLUE}🔍 Verifying cluster status...${NC}"
echo "  Waiting for nodes to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s > /dev/null 2>&1
check_command "All nodes are ready"

# Display cluster info
echo -e "${BLUE}📊 Cluster information:${NC}"
kubectl cluster-info
echo ""

# Step 8: Create namespace
echo -e "${BLUE}📁 Setting up Kubernetes namespace...${NC}"
if ! kubectl get namespace xploreml > /dev/null 2>&1; then
    kubectl create namespace xploreml > /dev/null 2>&1
    kubectl label namespace xploreml app=xploreml environment=production > /dev/null 2>&1
    check_command "Namespace 'xploreml' created"
else
    echo -e "${YELLOW}  Namespace 'xploreml' already exists${NC}"
fi

# Step 9: Create Kubernetes service account with Workload Identity
echo -e "${BLUE}🔐 Setting up Workload Identity...${NC}"
kubectl create serviceaccount xploreml-ksa --namespace=xploreml > /dev/null 2>&1 || true

kubectl annotate serviceaccount xploreml-ksa \
    --namespace=xploreml \
    iam.gke.io/gcp-service-account=xploreml-sa@$PROJECT_ID.iam.gserviceaccount.com > /dev/null 2>&1 || true

gcloud iam service-accounts add-iam-policy-binding \
    xploreml-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:$PROJECT_ID.svc.id.goog[xploreml/xploreml-ksa]" > /dev/null 2>&1 || true

check_command "Workload Identity configured"

# Step 10: Install useful cluster tools
echo -e "${BLUE}🛠️ Installing cluster utilities...${NC}"

# Install metrics server if not present
if ! kubectl get deployment metrics-server -n kube-system > /dev/null 2>&1; then
    echo "  Installing metrics server..."
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml > /dev/null 2>&1
    check_command "Metrics server installed"
fi

# Step 11: Create ConfigMap for XploreML
echo -e "${BLUE}⚙️ Creating XploreML configuration...${NC}"
kubectl create configmap xploreml-config \
    --namespace=xploreml \
    --from-literal=PROJECT_ID=$PROJECT_ID \
    --from-literal=CLUSTER_NAME=$CLUSTER_NAME \
    --from-literal=ZONE=$ZONE \
    --from-literal=ENVIRONMENT=production \
    --dry-run=client -o yaml | kubectl apply -f - > /dev/null 2>&1

check_command "XploreML configuration created"

# Step 12: Final verification
echo -e "${BLUE}🔍 Final verification...${NC}"
echo "  Checking nodes:"
kubectl get nodes --no-headers | while read line; do
    echo -e "    ${GREEN}✅${NC} $line"
done

echo "  Checking namespaces:"
kubectl get namespace xploreml --no-headers | while read line; do
    echo -e "    ${GREEN}✅${NC} $line"
done

echo "  Checking storage buckets:"
for bucket in "${buckets[@]}"; do
    if gsutil ls gs://$bucket > /dev/null 2>&1; then
        echo -e "    ${GREEN}✅${NC} gs://$bucket"
    fi
done

# Success summary
echo ""
echo -e "${GREEN}🎉 XploreML GKE cluster setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Cluster Summary:${NC}"
echo -e "  ${PURPLE}Project ID:${NC} $PROJECT_ID"
echo -e "  ${PURPLE}Cluster Name:${NC} $CLUSTER_NAME"
echo -e "  ${PURPLE}Zone:${NC} $ZONE"
echo -e "  ${PURPLE}Nodes:${NC} $(kubectl get nodes --no-headers | wc -l)"
echo -e "  ${PURPLE}Machine Type:${NC} $MACHINE_TYPE"
echo -e "  ${PURPLE}Auto-scaling:${NC} $MIN_NODES - $MAX_NODES nodes"
echo ""

echo -e "${BLUE}🚀 Ready for XploreML deployment!${NC}"
echo ""
echo -e "${BLUE}📝 Next steps:${NC}"
echo -e "  1. ${YELLOW}Deploy XploreML:${NC} ./scripts/deploy.sh --environment production --project $PROJECT_ID"
echo -e "  2. ${YELLOW}Check status:${NC} kubectl get pods -n xploreml"
echo -e "  3. ${YELLOW}Get service URL:${NC} kubectl get service -n xploreml"
echo ""

echo -e "${BLUE}💡 Useful commands:${NC}"
echo -e "  ${YELLOW}Cluster info:${NC} kubectl cluster-info"
echo -e "  ${YELLOW}Node status:${NC} kubectl get nodes"
echo -e "  ${YELLOW}Namespace pods:${NC} kubectl get pods -n xploreml"
echo -e "  ${YELLOW}Cluster credentials:${NC} gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE"
echo ""

echo -e "${GREEN}✨ Your XploreML infrastructure is ready! ✨${NC}"