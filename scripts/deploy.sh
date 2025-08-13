#!/bin/bash
# scripts/deploy.sh - XploreML Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
ENVIRONMENT="staging"
PROJECT_ID="xploreml"
CLUSTER_NAME="xploreml"
CLUSTER_ZONE="us-central1"
IMAGE_TAG="latest"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -c|--cluster)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        -z|--zone)
            CLUSTER_ZONE="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -h|--help)
            echo "XploreML Deployment Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -e, --environment    Deployment environment (staging|production) [default: staging]"
            echo "  -p, --project        GCP Project ID"
            echo "  -c, --cluster        GKE Cluster name [default: xploreml-cluster]"
            echo "  -z, --zone           GKE Cluster zone [default: us-central1-a]"
            echo "  -t, --tag            Docker image tag [default: latest]"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --environment production --project my-gcp-project"
            echo "  $0 -e staging -p my-project -t v2.0.0"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo -e "${RED}❌ Environment must be 'staging' or 'production'${NC}"
    exit 1
fi

# Get project ID if not provided
if [ -z "$PROJECT_ID" ]; then
    echo -e "${BLUE}🔍 Detecting GCP Project ID...${NC}"
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ Could not detect GCP Project ID. Please provide with -p flag${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}🚀 Deploying XploreML to $ENVIRONMENT environment${NC}"
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "  Environment: $ENVIRONMENT"
echo -e "  Project ID: $PROJECT_ID"
echo -e "  Cluster: $CLUSTER_NAME"
echo -e "  Zone: $CLUSTER_ZONE"
echo -e "  Image Tag: $IMAGE_TAG"
echo ""

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is required but not installed${NC}"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is required but not installed${NC}"
    exit 1
fi

# Check if kustomize is available
if ! command -v kustomize &> /dev/null; then
    echo -e "${YELLOW}⚠️  kustomize not found, installing...${NC}"
    # Install kustomize
    curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
    sudo mv kustomize /usr/local/bin/
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Authenticate with GCP
echo -e "${BLUE}🔐 Setting up GCP authentication...${NC}"
gcloud config set project $PROJECT_ID
gcloud auth configure-docker

# Get GKE credentials
echo -e "${BLUE}🔑 Getting GKE credentials...${NC}"
gcloud container clusters get-credentials $CLUSTER_NAME --zone $CLUSTER_ZONE --project $PROJECT_ID

# Build and push Docker image
echo -e "${BLUE}🐳 Building and pushing Docker image...${NC}"
IMAGE_NAME="gcr.io/$PROJECT_ID/xploreml:$IMAGE_TAG"

docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME

echo -e "${GREEN}✅ Docker image pushed: $IMAGE_NAME${NC}"

# Deploy to Kubernetes
echo -e "${BLUE}⚓ Deploying to Kubernetes...${NC}"

# Navigate to the appropriate overlay
OVERLAY_PATH="k8s/overlays/$ENVIRONMENT"

if [ ! -d "$OVERLAY_PATH" ]; then
    echo -e "${RED}❌ Overlay directory not found: $OVERLAY_PATH${NC}"
    exit 1
fi

cd $OVERLAY_PATH

# Update image in kustomization
echo -e "${BLUE}🔧 Updating image reference...${NC}"
kustomize edit set image xploreml=$IMAGE_NAME

# Apply the configuration
echo -e "${BLUE}🚀 Applying Kubernetes manifests...${NC}"
kubectl apply -k .

# Wait for deployment to complete
echo -e "${BLUE}⏳ Waiting for deployment to complete...${NC}"
NAMESPACE="xploreml"
if [ "$ENVIRONMENT" = "staging" ]; then
    NAMESPACE="xploreml-staging"
fi

kubectl rollout status deployment/xploreml-app -n $NAMESPACE --timeout=600s

# Verify deployment
echo -e "${BLUE}🔍 Verifying deployment...${NC}"
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE

# Get service URL
if [ "$ENVIRONMENT" = "production" ]; then
    #INGRESS_IP=$(kubectl get ingress xploreml-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    #echo -e "${GREEN}🌐 Production URL: https://xploreml.yourdomain.com${NC}"
    #echo -e "${BLUE}📍 Ingress IP: $INGRESS_IP${NC}"
else
    SERVICE_IP=$(kubectl get service xploreml-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    echo -e "${GREEN}🌐 Staging URL: http://$SERVICE_IP (if LoadBalancer)${NC}"
fi

# Run health check
echo -e "${BLUE}🏥 Running health check...${NC}"
sleep 30  # Wait for pods to be fully ready

POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=xploreml -o jsonpath='{.items[0].metadata.name}')
HEALTH_CHECK=$(kubectl exec $POD_NAME -n $NAMESPACE -- curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/_stcore/health 2>/dev/null || echo "000")

if [ "$HEALTH_CHECK" = "200" ]; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Health check returned: $HEALTH_CHECK${NC}"
fi

echo -e "${GREEN}🎉 XploreML deployment to $ENVIRONMENT completed successfully!${NC}"

# Deployment summary
echo ""
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo -e "  Environment: $ENVIRONMENT"
echo -e "  Image: $IMAGE_NAME"
echo -e "  Namespace: $NAMESPACE"
echo -e "  Pods: $(kubectl get pods -n $NAMESPACE --no-headers | wc -l)"
echo -e "  Status: $(kubectl get deployment xploreml-app -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Available")].status}')"

# Show logs command
echo ""
echo -e "${BLUE}📝 Useful commands:${NC}"
echo -e "  View logs: ${YELLOW}kubectl logs -f deployment/xploreml-app -n $NAMESPACE${NC}"
echo -e "  Scale up: ${YELLOW}kubectl scale deployment xploreml-app --replicas=3 -n $NAMESPACE${NC}"
echo -e "  Port forward: ${YELLOW}kubectl port-forward service/xploreml-service 8501:80 -n $NAMESPACE${NC}"

---
