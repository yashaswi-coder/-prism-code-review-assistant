import java.sql.Connection;
import java.sql.PreparedStatement;

class CleanPreparedStatementCase {
    void findUser(Connection connection, String userInput) throws Exception {
        String query = "SELECT * FROM users WHERE name = ?";
        try (PreparedStatement statement = connection.prepareStatement(query)) {
            statement.setString(1, userInput);
            statement.executeQuery();
        }
    }
}
