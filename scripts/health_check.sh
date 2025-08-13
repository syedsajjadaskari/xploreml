#!/bin/bash
# scripts/health_check.sh - XploreML Health Check Script

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE=${1:-xploreml}
SERVICE_NAME=${2:-xploreml-service}

echo -e "${BLUE}🏥 Running XploreML health check...${NC}"

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ Namespace $NAMESPACE not found${NC}"
    exit 1
fi

# Check deployment status
echo -e "${BLUE}📋 Checking deployment status...${NC}"
DEPLOYMENT_STATUS=$(kubectl get deployment xploreml-app -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "Unknown")

if [ "$DEPLOYMENT_STATUS" = "True" ]; then
    echo -e "${GREEN}✅ Deployment is available${NC}"
else
    echo -e "${RED}❌ Deployment is not available: $DEPLOYMENT_STATUS${NC}"
fi

# Check pod status
echo -e "${BLUE}📦 Checking pod status...${NC}"
READY_PODS=$(kubectl get pods -n $NAMESPACE -l app=xploreml --no-headers | grep "Running" | grep "1/1" | wc -l)
TOTAL_PODS=$(kubectl get pods -n $NAMESPACE -l app=xploreml --no-headers | wc -l)

echo -e "${BLUE}Pods ready: $READY_PODS/$TOTAL_PODS${NC}"

if [ "$READY_PODS" -gt 0 ]; then
    echo -e "${GREEN}✅ At least one pod is ready${NC}"
else
    echo -e "${RED}❌ No pods are ready${NC}"
    kubectl get pods -n $NAMESPACE -l app=xploreml
fi

# Check service
echo -e "${BLUE}🌐 Checking service...${NC}"
if kubectl get service $SERVICE_NAME -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✅ Service exists${NC}"
    SERVICE_TYPE=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.type}')
    echo -e "${BLUE}Service type: $SERVICE_TYPE${NC}"
else
    echo -e "${RED}❌ Service not found${NC}"
fi

# Health endpoint check
echo -e "${BLUE}🔍 Checking health endpoint...${NC}"
if [ "$READY_PODS" -gt 0 ]; then
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=xploreml -o jsonpath='{.items[0].metadata.name}')
    HEALTH_RESPONSE=$(kubectl exec $POD_NAME -n $NAMESPACE -- curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/_stcore/health 2>/dev/null || echo "000")
    
    if [ "$HEALTH_RESPONSE" = "200" ]; then
        echo -e "${GREEN}✅ Health endpoint responding${NC}"
    else
        echo -e "${YELLOW}⚠️  Health endpoint returned: $HEALTH_RESPONSE${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Cannot check health endpoint - no ready pods${NC}"
fi

# Resource usage check
echo -e "${BLUE}📊 Checking resource usage...${NC}"
kubectl top pods -n $NAMESPACE --no-headers 2>/dev/null | while read line; do
    if [[ $line == *"xploreml"* ]]; then
        echo -e "${BLUE}$line${NC}"
    fi
done

# Final summary
echo ""
echo -e "${BLUE}📋 Health Check Summary:${NC}"
echo -e "  Namespace: $NAMESPACE"
echo -e "  Deployment: $DEPLOYMENT_STATUS"
echo -e "  Ready Pods: $READY_PODS/$TOTAL_PODS"
echo -e "  Service: $([ $(kubectl get service $SERVICE_NAME -n $NAMESPACE &> /dev/null; echo $?) -eq 0 ] && echo "✅ Available" || echo "❌ Not found")"
echo -e "  Health Endpoint: $([ "$HEALTH_RESPONSE" = "200" ] && echo "✅ Healthy" || echo "⚠️  Check needed")"

if [ "$DEPLOYMENT_STATUS" = "True" ] && [ "$READY_PODS" -gt 0 ] && [ "$HEALTH_RESPONSE" = "200" ]; then
    echo -e "${GREEN}🎉 XploreML is healthy and running!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  XploreML may have issues - please investigate${NC}"
    exit 1
fi
