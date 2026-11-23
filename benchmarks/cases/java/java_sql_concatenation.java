import java.sql.Statement;

class SqlConcatenationCase {
    void findUser(Statement statement, String userInput) throws Exception {
        statement.executeQuery("SELECT * FROM users WHERE name='" + userInput);
    }
}
