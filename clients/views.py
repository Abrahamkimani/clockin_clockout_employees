from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Client
from .serializers import (
    ClientSerializer,
    ClientListSerializer,
    ClientCreateSerializer,
    ClientLocationSerializer
)


class ClientListView(generics.ListAPIView):
    """
    API endpoint for listing clients.
    """
    serializer_class = ClientListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Client.objects.filter(is_active=True)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(client_id__icontains=search) |
                Q(city__icontains=search)
            )
        
        # Filter by care level
        care_level = self.request.query_params.get('care_level')
        if care_level:
            queryset = queryset.filter(care_level=care_level)
        
        return queryset.order_by('last_name', 'first_name')


class ClientDetailView(generics.RetrieveAPIView):
    """
    API endpoint for getting detailed client information.
    """
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    queryset = Client.objects.all()
    lookup_field = 'id'


class ClientCreateView(generics.CreateAPIView):
    """
    API endpoint for creating new clients (admin/supervisor only).
    """
    serializer_class = ClientCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Check if user has permission to create clients
        if not (request.user.is_supervisor or request.user.is_staff):
            return Response({
                'error': 'Permission denied. Only supervisors can create clients.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().create(request, *args, **kwargs)


class ClientUpdateView(generics.UpdateAPIView):
    """
    API endpoint for updating client information (admin/supervisor only).
    """
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    queryset = Client.objects.all()
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        # Check if user has permission to update clients
        if not (request.user.is_supervisor or request.user.is_staff):
            return Response({
                'error': 'Permission denied. Only supervisors can update clients.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)


class ClientLocationView(generics.RetrieveAPIView):
    """
    API endpoint for getting client location information for GPS verification.
    """
    serializer_class = ClientLocationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Client.objects.filter(is_active=True)
    lookup_field = 'id'


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_search(request):
    """
    API endpoint for searching clients by various criteria.
    """
    query = request.query_params.get('q', '').strip()
    
    if not query:
        return Response({
            'results': [],
            'message': 'Please provide a search query'
        }, status=status.HTTP_200_OK)
    
    # Search in multiple fields
    clients = Client.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(client_id__icontains=query) |
        Q(street_address__icontains=query) |
        Q(city__icontains=query),
        is_active=True
    ).order_by('last_name', 'first_name')[:10]  # Limit to 10 results
    
    serializer = ClientListSerializer(clients, many=True)
    
    return Response({
        'results': serializer.data,
        'count': clients.count()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_clients(request):
    """
    API endpoint to find clients near a given location.
    """
    try:
        latitude = float(request.query_params.get('latitude'))
        longitude = float(request.query_params.get('longitude'))
        radius_km = float(request.query_params.get('radius', 5))  # Default 5km
    except (TypeError, ValueError):
        return Response({
            'error': 'Invalid latitude, longitude, or radius parameters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Simple bounding box calculation (for more accuracy, use proper geospatial queries)
    # 1 degree of latitude ≈ 111 km
    # 1 degree of longitude ≈ 111 km * cos(latitude)
    import math
    
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * math.cos(math.radians(latitude)))
    
    min_lat = latitude - lat_delta
    max_lat = latitude + lat_delta
    min_lng = longitude - lng_delta
    max_lng = longitude + lng_delta
    
    clients = Client.objects.filter(
        latitude__gte=min_lat,
        latitude__lte=max_lat,
        longitude__gte=min_lng,
        longitude__lte=max_lng,
        is_active=True
    ).order_by('last_name', 'first_name')
    
    # Calculate actual distance for each client
    client_data = []
    for client in clients:
        # Haversine formula for distance calculation
        client_lat = float(client.latitude)
        client_lng = float(client.longitude)
        
        dlat = math.radians(client_lat - latitude)
        dlng = math.radians(client_lng - longitude)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(latitude)) * math.cos(math.radians(client_lat)) * 
             math.sin(dlng/2) * math.sin(dlng/2))
        c = 2 * math.asin(math.sqrt(a))
        distance_km = 6371 * c  # Earth's radius in km
        
        if distance_km <= radius_km:
            client_info = ClientLocationSerializer(client).data
            client_info['distance_km'] = round(distance_km, 2)
            client_data.append(client_info)
    
    # Sort by distance
    client_data.sort(key=lambda x: x['distance_km'])
    
    return Response({
        'clients': client_data,
        'search_location': {
            'latitude': latitude,
            'longitude': longitude
        },
        'radius_km': radius_km,
        'count': len(client_data)
    }, status=status.HTTP_200_OK)
