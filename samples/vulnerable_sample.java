import java.security.MessageDigest;
import java.sql.Statement;

class VulnerableSample {
    private static final String API_TOKEN = "demo-token-123";

    String hash(String input) throws Exception {
        return MessageDigest.getInstance("MD5").digest(input.getBytes()).toString();
    }

    void runCommand(String command) throws Exception {
        Runtime.getRuntime().exec(command);
    }

    void findUser(Statement statement, String userInput) throws Exception {
        statement.executeQuery("SELECT * FROM users WHERE name='" + userInput);
    }
}
