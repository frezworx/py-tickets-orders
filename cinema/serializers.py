from rest_framework import serializers

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, \
    Ticket


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieListSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    # actors = serializers.Acto(
    #     many=True, read_only=True, slug_field="full_name"
    # )
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = (
            "id", "title", "description", "duration", "genres", "actors"
        )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
        )


class TicketTakenSeatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )

    taken_seats = TicketTakenSeatsSerializer(
        many=True,
        source="tickets"
    )

    tickets_available = serializers.IntegerField(
         read_only=True
    )

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "taken_seats",
            "tickets_available"
        )


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionDetailSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ("tickets",)

    def create(self, validated_data):
        tickets_data = validated_data.pop(
            "tickets")  # Извлекаем данные билетов
        order = Order.objects.create(**validated_data)  # Создаем заказ
        for ticket_data in tickets_data:
            Ticket.objects.create(order=order,
                                  **ticket_data)  # Создаем каждый билет
        return order


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "user", "tickets", "created_at")
