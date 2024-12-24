from django.db.models import Q, Count, F, ExpressionWrapper
from django.db.models.fields import IntegerField
from django.db.models.functions import TruncDate
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, \
    Ticket

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderListSerializer, TicketSerializer,
    OrderCreateSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset.prefetch_related()

        actors = self.request.query_params.get("actors")
        if actors:
            actor_names = actors.split(",")
            query = Q()
            for name in actor_names:
                query |= Q(actors__first_name__icontains=name) | Q(
                    actors__last_name__icontains=name
                )
            queryset = queryset.filter(query)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(
                title__icontains=title
            )

        genres = self.request.query_params.get("genres")
        if genres:
            queryset = queryset.filter(
                genres__name__icontains=genres.split(",")
            )

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    @staticmethod
    def get_format_show_time(self):
        pass

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("movie")

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.annotate(
                date=TruncDate("show_time")
            ).filter(date=date)

        if movie:
            queryset = queryset.filter(movie=movie)

        if self.action == "retrieve":
            queryset = queryset.select_related("cinema_hall").annotate(
                capacity=F("cinema_hall__rows") * F(
                    "cinema_hall__seats_in_row"),
                tickets_available=ExpressionWrapper(
                    F("capacity") - Count("tickets"),
                    output_field=IntegerField(),
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderSetPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session")

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
