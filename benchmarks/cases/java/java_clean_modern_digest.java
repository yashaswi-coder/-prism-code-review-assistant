import java.security.MessageDigest;

class CleanModernDigestCase {
    byte[] hash(byte[] input) throws Exception {
        return MessageDigest.getInstance("SHA-256").digest(input);
    }
}
